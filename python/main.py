
from pathlib import Path
import sys

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
IMAGES = ROOT / "images"
SQL = ROOT / "sql" / "analysis.sql"

FILES = {
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
}

MIN_PREVIOUS_REVENUE = 10000


def draw_line(df, x, y, title, xlabel, filename):
    if df.empty:
        print(f"Skipped empty chart: {filename}")
        return

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(
        df[x].astype(str),
        df[y],
        marker="o",
        linewidth=2
    )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(
        "Growth (%)" if y == "growth_pct" else "Revenue (BRL)"
    )

    ax.tick_params(axis="x", labelrotation=55)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(IMAGES / filename, dpi=160)
    plt.close(fig)


def draw_bar(df, label, value, title, filename):
    if df.empty:
        print(f"Skipped empty chart: {filename}")
        return

    fig, ax = plt.subplots(figsize=(11, 6))

    data = df.sort_values(value)

    ax.barh(
        data[label].fillna("Unknown").astype(str),
        data[value]
    )

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Revenue (BRL)")
    ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()
    fig.savefig(IMAGES / filename, dpi=160)
    plt.close(fig)


def draw_growth_chart(growth_df, monthly_sales_df):
    """
    Plot monthly revenue growth only when the previous month's
    revenue is at least R$10,000.

    This avoids misleading percentage spikes caused by a very
    small revenue base in the early dataset months.
    """

    growth = growth_df.copy()
    sales = monthly_sales_df.copy()

    growth["month"] = growth["month"].astype(str)
    sales["month"] = sales["month"].astype(str)

    growth["growth_pct"] = pd.to_numeric(
        growth["growth_pct"], errors="coerce"
    )

    sales["revenue"] = pd.to_numeric(
        sales["revenue"], errors="coerce"
    )

    sales = sales.sort_values("month")
    sales["previous_revenue"] = sales["revenue"].shift(1)

    growth = growth.merge(
        sales[["month", "previous_revenue"]],
        on="month",
        how="left"
    )

    growth = growth[
        (growth["previous_revenue"] >= MIN_PREVIOUS_REVENUE)
        & growth["growth_pct"].notna()
    ].copy()

    growth = growth.sort_values("month")

    if growth.empty:
        print("Skipped monthly growth chart: no eligible months.")
        return

    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(
        growth["month"],
        growth["growth_pct"],
        marker="o",
        linewidth=2
    )

    ax.axhline(0, color="gray", linewidth=1)

    ax.set_title(
        "Monthly Revenue Growth (%)",
        fontsize=14,
        fontweight="bold"
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Growth (%)")

    ax.tick_params(axis="x", labelrotation=55)
    ax.grid(alpha=0.25)

    fig.text(
        0.5,
        0.01,
        "Growth shown only when previous-month revenue >= R$10,000",
        ha="center",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.04, 1, 1])

    fig.savefig(
        IMAGES / "monthly_growth.png",
        dpi=160
    )

    plt.close(fig)


def main():
    missing = [
        name
        for name in FILES.values()
        if not (DATA / name).is_file()
    ]

    if missing:
        print("Missing CSV files in the data folder:")

        for name in missing:
            print("  -", name)

        print("Copy your existing Olist CSV files into:", DATA)
        return 1

    RESULTS.mkdir(exist_ok=True)
    IMAGES.mkdir(exist_ok=True)

    con = duckdb.connect(database=":memory:")

    try:
        # Load CSV datasets as DuckDB views.
        for table, filename in FILES.items():
            csv = (
                (DATA / filename)
                .as_posix()
                .replace("'", "''")
            )

            con.execute(
                f"CREATE VIEW {table} AS "
                f"SELECT * FROM read_csv_auto("
                f"'{csv}', header=true, all_varchar=true)"
            )

            count = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            print(f"Loaded {table}: {count:,} rows")

        # Run SQL analysis queries.
        script = SQL.read_text(encoding="utf-8")
        parts = script.split("-- name: ")

        con.execute(parts[0])

        frames = {}

        for part in parts[1:]:
            name, _, query = part.partition("\n")
            name = name.strip()

            df = con.execute(query.strip()).df()

            df.to_csv(
                RESULTS / f"{name}.csv",
                index=False
            )

            frames[name] = df

            print(
                f"Saved results/{name}.csv "
                f"({len(df):,} rows)"
            )

        # Generate charts.
        draw_line(
            frames["monthly_sales"],
            "month",
            "revenue",
            "Monthly Delivered Sales Revenue",
            "Month",
            "monthly_revenue.png"
        )

        draw_bar(
            frames["top_categories"],
            "category",
            "revenue",
            "Top 10 Product Categories",
            "top_categories.png"
        )

        draw_bar(
            frames["state_sales"].head(15),
            "state",
            "revenue",
            "Top 15 Customer States by Revenue",
            "sales_by_state.png"
        )

        draw_growth_chart(
            frames["monthly_growth"],
            frames["monthly_sales"]
        )

        # Save summary report.
        summary = frames["summary"].iloc[0].to_dict()

        lines = [
            "E-Commerce Sales Analysis",
            "Delivered orders; item prices exclude freight",
            ""
        ]

        lines += [
            f"{key}: {value}"
            for key, value in summary.items()
        ]

        lines += [
            "",
            "Data source: Olist Brazilian E-Commerce Public Dataset",
            "SQL engine: DuckDB",
            "Revenue currency: Brazilian real (BRL)",
            "",
            "Monthly growth chart note:",
            "Growth comparisons are plotted only when",
            "previous-month revenue is at least R$10,000.",
            "The original monthly growth CSV is unchanged."
        ]

        (RESULTS / "summary.txt").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8"
        )

        print("\nSUCCESS")

        return 0

    finally:
        con.close()


if __name__ == "__main__":
    try:
        sys.exit(main())

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

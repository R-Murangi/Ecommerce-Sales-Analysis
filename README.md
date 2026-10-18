# E-Commerce Sales Analysis

Sales analysis of the **Olist Brazilian E-Commerce Public Dataset** using Python and DuckDB SQL. The project reads CSV files locally, uses SQL joins and aggregations, and generates reports and charts. No MySQL installation is needed.

## Dataset
Download the [Olist dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and copy these four original CSV files into `data/`:

- `olist_customers_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`

Raw datasets are not included in this repository.

## Run on Windows

1. Install Python 3.10+ and make sure `python` works in a terminal.
2. Copy the four CSV files into `data/`.
3. Double-click `run_project.bat` or run:

```powershell
python -m pip install -r requirements.txt
python python/main.py
```

Generated files appear in `images/` (PNG charts) and `results/` (CSV summaries and `summary.txt`). The folders start empty.

## Analysis

The SQL in `sql/analysis.sql` creates a `delivered_sales` view by joining customers, orders, order items and products. Reports include monthly revenue, top product categories, state revenue, top products, repeat customer rate and month-on-month revenue growth.

**Methodology:** Revenue is the sum of item prices for *delivered* orders, excluding freight. The order date is used for monthly grouping. Product categories are in the dataset's original Portuguese. Currency is BRL. Results depend on the dataset version.

## Project structure

```text
Ecommerce-Sales-Analysis/
  data/                 Your four CSV files (not provided)
  images/               Generated charts
  results/              Generated CSV reports
  python/main.py        Run SQL and create visualisations
  sql/analysis.sql      SQL analysis queries
  requirements.txt
  run_project.bat
  README.md
```

## Troubleshooting

- Missing CSV error: check that filenames are exact and CSVs are in `data/`.
- `python` not recognised: install Python and enable **Add Python to PATH**.
- Installation error: run `python -m pip install -r requirements.txt` and review the terminal output.

## Portfolio note

Review the generated reports and add your own findings and interpretation to this README before publishing. Avoid uploading the original large dataset files to GitHub.

-- DuckDB SQL analysis. The Python runner creates four views from your local Olist CSV files.
-- Revenue refers to item price (excluding freight) on delivered orders.
CREATE OR REPLACE VIEW delivered_sales AS
SELECT oi.order_id, oi.order_item_id, oi.product_id,
       TRY_CAST(oi.price AS DOUBLE) AS price,
       TRY_CAST(oi.freight_value AS DOUBLE) AS freight_value,
       TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP) AS purchase_date,
       c.customer_unique_id, c.customer_state,
       COALESCE(p.product_category_name, 'Uncategorised') AS category
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered';

-- name: summary
SELECT COUNT(DISTINCT order_id) AS total_orders,
       COUNT(*) AS items_sold,
       ROUND(SUM(price), 2) AS revenue,
       ROUND(SUM(price) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS average_order_value
FROM delivered_sales;

-- name: monthly_sales
SELECT strftime(purchase_date, '%Y-%m') AS month,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(price), 2) AS revenue
FROM delivered_sales
WHERE purchase_date IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- name: top_categories
SELECT category, COUNT(*) AS items_sold, ROUND(SUM(price), 2) AS revenue
FROM delivered_sales
GROUP BY 1 ORDER BY revenue DESC LIMIT 10;

-- name: state_sales
SELECT customer_state AS state,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(price), 2) AS revenue
FROM delivered_sales
GROUP BY 1 ORDER BY revenue DESC;

-- name: top_products
SELECT product_id, COUNT(*) AS units_sold, ROUND(SUM(price), 2) AS revenue
FROM delivered_sales
GROUP BY 1 ORDER BY revenue DESC LIMIT 10;

-- name: repeat_customers
WITH customer_orders AS (
  SELECT customer_unique_id, COUNT(DISTINCT order_id) AS orders
  FROM delivered_sales GROUP BY 1
)
SELECT COUNT(*) AS customers,
       COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE orders > 1) / NULLIF(COUNT(*), 0), 2) AS repeat_rate_pct
FROM customer_orders;

-- name: monthly_growth
WITH monthly AS (
  SELECT strftime(purchase_date, '%Y-%m') AS month, SUM(price) AS revenue
  FROM delivered_sales WHERE purchase_date IS NOT NULL GROUP BY 1
), prev AS (
  SELECT month, revenue, LAG(revenue) OVER (ORDER BY month) AS previous_revenue
  FROM monthly
)
SELECT month, ROUND(revenue, 2) AS revenue,
       ROUND(100.0 * (revenue - previous_revenue) / NULLIF(previous_revenue, 0), 2) AS growth_pct
FROM prev ORDER BY month;

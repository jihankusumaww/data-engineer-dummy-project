-- Contoh query analitik di atas star schema (buka dengan `sqlite3 data/warehouse.db`)

-- 1. Total revenue per kategori produk
SELECT
    p.category,
    SUM(f.total_amount) AS total_revenue,
    COUNT(f.order_id) AS total_orders
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 2. Top 5 customer berdasarkan total belanja
SELECT
    c.customer_name,
    c.city,
    SUM(f.total_amount) AS total_spent,
    COUNT(f.order_id) AS total_orders
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY total_spent DESC
LIMIT 5;

-- 3. Tren revenue harian
SELECT
    d.full_date,
    SUM(f.total_amount) AS daily_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.full_date
ORDER BY d.full_date;

-- 4. Produk terlaris (by quantity)
SELECT
    p.product_name,
    SUM(f.quantity) AS total_qty_sold
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_qty_sold DESC;

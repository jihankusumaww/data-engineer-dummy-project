-- Star schema sederhana untuk data warehouse penjualan
-- Database: SQLite (tidak perlu server terpisah, cocok untuk portofolio)

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_customer (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name   TEXT NOT NULL,
    customer_email  TEXT NOT NULL UNIQUE,
    city            TEXT
);

CREATE TABLE dim_product (
    product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit_price      REAL NOT NULL,
    UNIQUE(product_name, unit_price)
);

CREATE TABLE dim_date (
    date_id         INTEGER PRIMARY KEY,   -- format YYYYMMDD
    full_date       TEXT NOT NULL,
    year            INTEGER,
    month           INTEGER,
    day             INTEGER,
    day_of_week     TEXT
);

CREATE TABLE fact_sales (
    order_id        INTEGER PRIMARY KEY,
    date_id         INTEGER REFERENCES dim_date(date_id),
    customer_id     INTEGER REFERENCES dim_customer(customer_id),
    product_id      INTEGER REFERENCES dim_product(product_id),
    quantity        INTEGER NOT NULL,
    unit_price      REAL NOT NULL,
    total_amount    REAL NOT NULL
);

CREATE INDEX idx_fact_date ON fact_sales(date_id);
CREATE INDEX idx_fact_customer ON fact_sales(customer_id);
CREATE INDEX idx_fact_product ON fact_sales(product_id);

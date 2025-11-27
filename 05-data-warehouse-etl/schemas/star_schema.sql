-- Data Warehouse Star Schema
-- Implements Kimball dimensional modeling

-- Date Dimension
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    day INTEGER,
    month INTEGER,
    quarter INTEGER,
    year INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year INTEGER,
    fiscal_quarter INTEGER
);

-- Customer Dimension (SCD Type 2)
CREATE TABLE dim_customer (
    customer_key SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(50),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    customer_segment VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product Dimension
CREATE TABLE dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(200),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    unit_price DECIMAL(10, 2),
    cost DECIMAL(10, 2),
    supplier_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Location Dimension
CREATE TABLE dim_location (
    location_key SERIAL PRIMARY KEY,
    location_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(200),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    region VARCHAR(100),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT TRUE
);

-- Orders Fact Table
CREATE TABLE fact_orders (
    order_key BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date_key INTEGER REFERENCES dim_date(date_key),
    customer_key INTEGER REFERENCES dim_customer(customer_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    location_key INTEGER REFERENCES dim_location(location_key),
    order_quantity INTEGER,
    unit_price DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2),
    tax_amount DECIMAL(10, 2),
    shipping_cost DECIMAL(10, 2),
    total_amount DECIMAL(12, 2),
    payment_method VARCHAR(50),
    order_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_fact_orders_date ON fact_orders(order_date_key);
CREATE INDEX idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX idx_fact_orders_product ON fact_orders(product_key);
CREATE INDEX idx_fact_orders_location ON fact_orders(location_key);
CREATE INDEX idx_fact_orders_order_id ON fact_orders(order_id);

-- Partitioning by date (for large fact tables)
-- ALTER TABLE fact_orders PARTITION BY RANGE (order_date_key);

-- Aggregation Table: Daily Sales Summary
CREATE TABLE agg_daily_sales (
    date_key INTEGER REFERENCES dim_date(date_key),
    location_key INTEGER REFERENCES dim_location(location_key),
    product_key INTEGER REFERENCES dim_product(product_key),
    total_orders INTEGER,
    total_quantity INTEGER,
    total_revenue DECIMAL(12, 2),
    total_cost DECIMAL(12, 2),
    total_profit DECIMAL(12, 2),
    avg_order_value DECIMAL(10, 2),
    PRIMARY KEY (date_key, location_key, product_key)
);

CREATE INDEX idx_agg_daily_sales_date ON agg_daily_sales(date_key);
CREATE INDEX idx_agg_daily_sales_location ON agg_daily_sales(location_key);


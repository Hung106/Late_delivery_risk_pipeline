CREATE DATABASE warehouse_db;

CREATE TABLE customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(100),
    customer_state CHAR(2)
);

CREATE TABLE geolocation (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat DOUBLE PRECISION,
    geolocation_lng DOUBLE PRECISION,
    geolocation_city VARCHAR(100),
    geolocation_state CHAR(2)
);

CREATE TABLE order_items (
    order_id VARCHAR(32) NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(32) NOT NULL,
    seller_id VARCHAR(32) NOT NULL,
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10,2),
    freight_value NUMERIC(10,2),

    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE order_payments (
    order_id VARCHAR(32) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(30),
    payment_installments INTEGER,
    payment_value NUMERIC(10,2),

    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE order_reviews (
    review_id VARCHAR(32),
    order_id VARCHAR(32),
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL,
    order_status VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER
);

CREATE TABLE sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(100),
    seller_state CHAR(2)
);

CREATE TABLE product_category_name_translation (
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS pipeline_run_history (
    run_id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100),
    table_name VARCHAR(100),
    load_type VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    rows_extracted INT,
    status VARCHAR(50),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS pipeline_metadata (
    table_name VARCHAR(100) PRIMARY KEY,
    load_type VARCHAR(50),
    watermark_column VARCHAR(100),
    last_watermark VARCHAR(255),
    last_batch_id VARCHAR(100),
    last_run_time TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO pipeline_metadata
(
 table_name,
 load_type,
 watermark_column
)
VALUES

('customers','full',NULL),

('geolocation','full',NULL),

('orders','incremental','order_purchase_timestamp'),

('order_items','incremental','order_purchase_timestamp'),

('order_payments','full',NULL),

('order_reviews','incremental','review_creation_date'),

('products','full',NULL),

('sellers','full',NULL),

('product_category_name_translation','full',NULL);
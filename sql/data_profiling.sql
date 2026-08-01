------------------------------------------------------------
-- CUSTOMERS
------------------------------------------------------------

-- Total records
SELECT COUNT(*) AS total_customers
FROM customers;

-- Check for duplicate customer_id
SELECT customer_id, COUNT(*)
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- NULL values
SELECT
    COUNT(*) FILTER (WHERE customer_id IS NULL) AS null_customer_id,
    COUNT(*) FILTER (WHERE customer_unique_id IS NULL) AS null_customer_unique_id,
    COUNT(*) FILTER (WHERE customer_zip_code_prefix IS NULL) AS null_zip,
    COUNT(*) FILTER (WHERE customer_city IS NULL) AS null_city,
    COUNT(*) FILTER (WHERE customer_state IS NULL) AS null_state
FROM customers;

-- Customer distribution by state
SELECT
    customer_state,
    COUNT(*) AS total
FROM customers
GROUP BY customer_state
ORDER BY total DESC;


------------------------------------------------------------
-- GEOLOCATION
------------------------------------------------------------

SELECT COUNT(*) AS total_rows
FROM geolocation;

SELECT
    COUNT(*) FILTER (WHERE geolocation_zip_code_prefix IS NULL) AS null_zip,
    COUNT(*) FILTER (WHERE geolocation_lat IS NULL) AS null_lat,
    COUNT(*) FILTER (WHERE geolocation_lng IS NULL) AS null_lng
FROM geolocation;

-- Invalid latitude
SELECT COUNT(*)
FROM geolocation
WHERE geolocation_lat NOT BETWEEN -90 AND 90;

-- Invalid longitude
SELECT COUNT(*)
FROM geolocation
WHERE geolocation_lng NOT BETWEEN -180 AND 180;

-- Duplicate ZIP Code
SELECT
    geolocation_zip_code_prefix,
    COUNT(*)
FROM geolocation
GROUP BY geolocation_zip_code_prefix
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;


------------------------------------------------------------
-- ORDERS
------------------------------------------------------------

SELECT COUNT(*) AS total_orders
FROM orders;

-- Duplicate PK
SELECT order_id, COUNT(*)
FROM orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Order Status Distribution
SELECT
    order_status,
    COUNT(*) AS total
FROM orders
GROUP BY order_status
ORDER BY total DESC;

-- NULL timestamps
SELECT
    COUNT(*) FILTER (WHERE order_purchase_timestamp IS NULL) AS purchase_null,
    COUNT(*) FILTER (WHERE order_approved_at IS NULL) AS approved_null,
    COUNT(*) FILTER (WHERE order_delivered_carrier_date IS NULL) AS carrier_null,
    COUNT(*) FILTER (WHERE order_delivered_customer_date IS NULL) AS delivered_null
FROM orders;


------------------------------------------------------------
-- ORDER ITEMS
------------------------------------------------------------

SELECT COUNT(*) AS total_items
FROM order_items;

-- Duplicate Composite PK
SELECT
    order_id,
    order_item_id,
    COUNT(*)
FROM order_items
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;

-- Price Statistics
SELECT
    MIN(price),
    MAX(price),
    AVG(price)
FROM order_items;

-- Freight Statistics
SELECT
    MIN(freight_value),
    MAX(freight_value),
    AVG(freight_value)
FROM order_items;


------------------------------------------------------------
-- ORDER PAYMENTS
------------------------------------------------------------

SELECT COUNT(*) AS total_payments
FROM order_payments;

SELECT payment_type, COUNT(*)
FROM order_payments
GROUP BY payment_type
ORDER BY COUNT(*) DESC;

SELECT
    MIN(payment_value),
    MAX(payment_value),
    AVG(payment_value)
FROM order_payments;


------------------------------------------------------------
-- ORDER REVIEWS
------------------------------------------------------------

SELECT COUNT(*) AS total_reviews
FROM order_reviews;

SELECT review_score, COUNT(*)
FROM order_reviews
GROUP BY review_score
ORDER BY review_score;

SELECT
    COUNT(*) FILTER (WHERE review_comment_message IS NULL) AS no_comment
FROM order_reviews;


------------------------------------------------------------
-- PRODUCTS
------------------------------------------------------------

SELECT COUNT(*) AS total_products
FROM products;

SELECT
    COUNT(*) FILTER (WHERE product_category_name IS NULL) AS null_category,
    COUNT(*) FILTER (WHERE product_weight_g IS NULL) AS null_weight,
    COUNT(*) FILTER (WHERE product_length_cm IS NULL) AS null_length,
    COUNT(*) FILTER (WHERE product_height_cm IS NULL) AS null_height,
    COUNT(*) FILTER (WHERE product_width_cm IS NULL) AS null_width
FROM products;

SELECT
    MIN(product_weight_g),
    MAX(product_weight_g),
    AVG(product_weight_g)
FROM products;


------------------------------------------------------------
-- SELLERS
------------------------------------------------------------

SELECT COUNT(*) AS total_sellers
FROM sellers;

SELECT
    seller_state,
    COUNT(*)
FROM sellers
GROUP BY seller_state
ORDER BY COUNT(*) DESC;


------------------------------------------------------------
-- CATEGORY TRANSLATION
------------------------------------------------------------

SELECT COUNT(*) AS total_categories
FROM product_category_name_translation;

SELECT
    COUNT(*) FILTER (
        WHERE product_category_name_english IS NULL
    ) AS null_translation
FROM product_category_name_translation;
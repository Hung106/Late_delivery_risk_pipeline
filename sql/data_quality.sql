/*
====================================================
Rule:
    failed_count = 0  --> PASS
    failed_count > 0  --> FAIL
====================================================
*/


WITH quality_checks AS (

/*
====================================================
CUSTOMERS TABLE
====================================================
*/


-- DQ_CUSTOMERS_001
-- customer_id must not be NULL

SELECT
    'CUSTOMERS_001_customer_id_not_null' AS check_name,
    COUNT(*) AS failed_count
FROM customers
WHERE customer_id IS NULL


UNION ALL


-- DQ_CUSTOMERS_002
-- customer_id must be unique

SELECT
    'CUSTOMERS_002_customer_id_duplicate' AS check_name,
    COUNT(*) AS failed_count
FROM (
    SELECT customer_id
    FROM customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) t



UNION ALL


/*
====================================================
SELLERS TABLE
====================================================
*/


-- seller_id cannot be NULL

SELECT
    'SELLERS_001_seller_id_not_null',
    COUNT(*)
FROM sellers
WHERE seller_id IS NULL



UNION ALL


-- seller_id duplicate

SELECT
    'SELLERS_002_seller_id_duplicate',
    COUNT(*)
FROM (
    SELECT seller_id
    FROM sellers
    GROUP BY seller_id
    HAVING COUNT(*) > 1
)t



UNION ALL


/*
====================================================
PRODUCTS TABLE
====================================================
*/


-- product_id cannot be NULL

SELECT
    'PRODUCTS_001_product_id_not_null',
    COUNT(*)
FROM products
WHERE product_id IS NULL



UNION ALL


-- product dimension cannot be negative

SELECT
    'PRODUCTS_002_negative_dimension',
    COUNT(*)
FROM products
WHERE
    product_weight_g < 0
    OR product_length_cm < 0
    OR product_height_cm < 0
    OR product_width_cm < 0



UNION ALL


/*
====================================================
ORDERS TABLE
====================================================
*/


-- order_id cannot be NULL

SELECT
    'ORDERS_001_order_id_not_null',
    COUNT(*)
FROM orders
WHERE order_id IS NULL



UNION ALL


-- order_id duplicate

SELECT
    'ORDERS_002_order_id_duplicate',
    COUNT(*)
FROM (
    SELECT order_id
    FROM orders
    GROUP BY order_id
    HAVING COUNT(*) > 1
)t



UNION ALL


-- approved time cannot before purchase time

SELECT
    'ORDERS_003_invalid_purchase_approved_time',
    COUNT(*)
FROM orders
WHERE order_approved_at < order_purchase_timestamp



UNION ALL


-- delivered date cannot before purchase date

SELECT
    'ORDERS_004_invalid_delivery_time',
    COUNT(*)
FROM orders
WHERE order_delivered_customer_date < order_purchase_timestamp



UNION ALL


/*
====================================================
ORDER ITEMS TABLE
====================================================
*/


-- Composite key duplicate

SELECT
    'ORDER_ITEMS_001_duplicate_order_item',
    COUNT(*)
FROM (
    SELECT
        order_id,
        order_item_id
    FROM order_items
    GROUP BY
        order_id,
        order_item_id
    HAVING COUNT(*) > 1
)t



UNION ALL


-- price must be positive

SELECT
    'ORDER_ITEMS_002_invalid_price',
    COUNT(*)
FROM order_items
WHERE price <= 0



UNION ALL


-- freight cannot negative

SELECT
    'ORDER_ITEMS_003_invalid_freight',
    COUNT(*)
FROM order_items
WHERE freight_value < 0



UNION ALL


/*
====================================================
REFERENTIAL INTEGRITY
====================================================
*/


-- order_items must have existing product

SELECT
    'FK_001_order_items_product_missing',
    COUNT(*)
FROM order_items oi
LEFT JOIN products p
ON oi.product_id = p.product_id
WHERE p.product_id IS NULL



UNION ALL


-- order_items must have existing seller

SELECT
    'FK_002_order_items_seller_missing',
    COUNT(*)
FROM order_items oi
LEFT JOIN sellers s
ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL



UNION ALL


-- orders must have existing customer

SELECT
    'FK_003_orders_customer_missing',
    COUNT(*)
FROM orders o
LEFT JOIN customers c
ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL



UNION ALL


/*
====================================================
ORDER PAYMENTS
====================================================
*/


-- payment value must positive

SELECT
    'PAYMENT_001_invalid_payment_value',
    COUNT(*)
FROM order_payments
WHERE payment_value <= 0



UNION ALL


/*
====================================================
ORDER REVIEWS
====================================================
*/


-- review score must between 1 and 5

SELECT
    'REVIEW_001_invalid_review_score',
    COUNT(*)
FROM order_reviews
WHERE review_score NOT BETWEEN 1 AND 5


)


SELECT
    check_name,
    failed_count,
    CASE
        WHEN failed_count = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM quality_checks

ORDER BY status DESC, check_name;
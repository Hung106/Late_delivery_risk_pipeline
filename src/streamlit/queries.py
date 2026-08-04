import pandas as pd
from databricks import sql

from databricks_conn import get_connection


def query(sql_query):

    conn = get_connection()

    df = pd.read_sql(
        sql_query,
        conn
    )

    conn.close()

    return df


ALL_YEARS_LABEL = "Tất cả"


def _year_where(year, column="order_purchase_year"):
    """Mệnh đề WHERE theo năm. Trả về chuỗi rỗng nếu chọn 'Tất cả'."""
    if year == ALL_YEARS_LABEL or year is None:
        return ""
    return f"WHERE {column} = {int(year)}"


def _year_and(year, column="order_purchase_year"):
    """Mệnh đề AND theo năm, dùng khi đã có WHERE khác đứng trước."""
    if year == ALL_YEARS_LABEL or year is None:
        return ""
    return f"AND {column} = {int(year)}"


def get_available_years():
    """Danh sách các năm có dữ liệu thực tế, dùng để đổ vào bộ lọc năm trên sidebar."""
    sql_query = """
        SELECT DISTINCT order_purchase_year AS year
        FROM workspace.gold.fact_delivery_performance
        WHERE order_purchase_year IS NOT NULL
        ORDER BY year DESC
    """
    df = query(sql_query)
    return df["year"].astype(int).tolist()


def get_order_level_cte(year=ALL_YEARS_LABEL):
    """Hàm tạo CTE order_level với bộ lọc năm động."""
    where_clause = _year_where(year)

    return f"""
        WITH order_level AS (
            SELECT
                order_id,
                MAX(order_status)          AS order_status,
                MAX(is_delivery_late)      AS is_delivery_late,
                MAX(total_delivery_days)   AS total_delivery_days,
                MAX(avg_review_score)      AS avg_review_score,
                MAX(customer_state)        AS customer_state,
                MAX(customer_lat)          AS customer_lat,
                MAX(customer_lng)          AS customer_lng,
                MAX(order_purchase_date)   AS order_purchase_date,
                MAX(order_purchase_week)   AS order_purchase_week,
                MAX(order_purchase_month)  AS order_purchase_month,
                MAX(order_purchase_year)   AS order_purchase_year
            FROM workspace.gold.fact_delivery_performance
            {where_clause}
            GROUP BY order_id
        )
    """


def get_yearly_summary():
    """
    Tổng số đơn & tỷ lệ trễ theo TỪNG NĂM.
    Dùng cho biểu đồ so sánh hiệu suất giữa các năm (điều hướng chọn năm để
    đào sâu), không phụ thuộc vào bộ lọc năm hiện tại.
    """
    sql_query = """
        WITH order_level AS (
            SELECT
                order_id,
                MAX(is_delivery_late)    AS is_delivery_late,
                MAX(order_purchase_year) AS order_purchase_year
            FROM workspace.gold.fact_delivery_performance
            GROUP BY order_id
        )
        SELECT
            order_purchase_year AS year,
            COUNT(*) AS total_orders,
            ROUND(AVG(is_delivery_late) * 100, 2) AS late_rate
        FROM order_level
        WHERE order_purchase_year IS NOT NULL
        GROUP BY order_purchase_year
        ORDER BY order_purchase_year
    """
    return query(sql_query)


def get_overview(year=ALL_YEARS_LABEL):
    """
    Bộ chỉ số KPI tổng quan cho năm được chọn, so sánh (YoY) với năm liền
    trước. Nếu year = 'Tất cả', kỳ so sánh không tồn tại nên các delta sẽ
    trả về NULL (không có ý nghĩa khi gộp nhiều năm khác nhau).
    """
    if year == ALL_YEARS_LABEL:
        current_filter = ""
        previous_filter = "WHERE 1 = 0"
    else:
        y = int(year)
        current_filter = f"WHERE order_purchase_year = {y}"
        previous_filter = f"WHERE order_purchase_year = {y - 1}"

    sql_query = f"""

    WITH order_level AS (
        SELECT
            order_id,
            MAX(is_delivery_late)     AS is_delivery_late,
            MAX(total_delivery_days)  AS total_delivery_days,
            MAX(avg_review_score)     AS avg_review_score,
            MAX(distance_km)          AS distance_km,
            MAX(order_purchase_year)  AS order_purchase_year
        FROM workspace.gold.fact_delivery_performance
        GROUP BY order_id
    ),

    current_period AS (
        SELECT
            COUNT(*)                                AS total_orders,
            ROUND(AVG(is_delivery_late) * 100, 2)   AS late_delivery_rate,
            ROUND(AVG(total_delivery_days), 2)      AS avg_delivery_days,
            ROUND(AVG(avg_review_score), 2)         AS avg_review_score,
            ROUND(AVG(distance_km), 2)              AS avg_distance_km
        FROM order_level
        {current_filter}
    ),

    previous_period AS (
        SELECT
            ROUND(AVG(is_delivery_late) * 100, 2)   AS late_delivery_rate,
            ROUND(AVG(total_delivery_days), 2)      AS avg_delivery_days,
            ROUND(AVG(avg_review_score), 2)         AS avg_review_score
        FROM order_level
        {previous_filter}
    ),

    risk AS (
        SELECT
            ROUND(
                SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                2
            ) AS high_risk_rate
        FROM workspace.gold.fact_delivery_risk
        {current_filter}
    )

    SELECT
        c.total_orders,
        c.late_delivery_rate,
        c.avg_delivery_days,
        c.avg_review_score,
        c.avg_distance_km,
        r.high_risk_rate,

        ROUND(c.late_delivery_rate - p.late_delivery_rate, 2)  AS late_delivery_rate_delta,
        ROUND(c.avg_delivery_days  - p.avg_delivery_days, 2)   AS avg_delivery_days_delta,
        ROUND(c.avg_review_score   - p.avg_review_score, 2)    AS avg_review_score_delta

    FROM current_period c
    CROSS JOIN previous_period p
    CROSS JOIN risk r

    """

    return query(sql_query).iloc[0]


def get_risk_level_trend(year=ALL_YEARS_LABEL):
    """Xu hướng tỷ trọng rủi ro CAO/TRUNG BÌNH theo THÁNG (đủ mượt để đọc theo năm)."""
    year_filter_and = _year_and(year)

    sql_query = f"""

    SELECT

        order_purchase_month AS period,

        COUNT(*) AS total_items,

        ROUND(
            SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS high_risk_pct,

        ROUND(
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
            2
        ) AS medium_risk_pct

    FROM workspace.gold.fact_delivery_risk

    WHERE order_purchase_month IS NOT NULL
      {year_filter_and}

    GROUP BY order_purchase_month

    ORDER BY order_purchase_month

    """

    return query(sql_query)


def get_high_risk_watchlist(limit: int = 20, year=ALL_YEARS_LABEL):

    year_filter_and = _year_and(year, column="r.order_purchase_year")

    sql_query = f"""

    SELECT

        r.order_id,
        r.seller_id,
        r.customer_state,
        r.seller_state,
        r.distance_km,
        ROUND(r.seller_late_rate * 100, 2) AS seller_late_rate_pct,
        r.avg_processing_days,
        r.risk_score,
        r.order_purchase_date,
        f.order_status

    FROM workspace.gold.fact_delivery_risk r

    JOIN (
        -- CAST phòng trường hợp order_status ở bảng gốc là kiểu số (mã trạng
        -- thái) thay vì chuỗi; NOT IN so sánh với literal string bên dưới
        -- sẽ báo lỗi CAST_INVALID_INPUT nếu không ép kiểu tường minh ở đây.
        SELECT DISTINCT order_id, CAST(order_status AS STRING) AS order_status
        FROM workspace.gold.fact_delivery_performance
    ) f
        ON r.order_id = f.order_id

    WHERE r.risk_level = 'HIGH'
      AND f.order_status NOT IN ('delivered', 'canceled')
      {year_filter_and}

    ORDER BY r.risk_score DESC, r.order_purchase_date DESC

    LIMIT {limit}

    """

    return query(sql_query)


def get_late_rate_trend(year=ALL_YEARS_LABEL):
    """Xu hướng tỷ lệ giao trễ theo THÁNG."""
    sql_query = f"""

    {get_order_level_cte(year)}

    SELECT

        order_purchase_month AS period,

        COUNT(*) AS total_orders,

        ROUND(AVG(is_delivery_late) * 100, 2) AS late_rate

    FROM order_level

    WHERE order_purchase_month IS NOT NULL

    GROUP BY order_purchase_month

    ORDER BY order_purchase_month

    """

    return query(sql_query)


def get_delivery_status(year=ALL_YEARS_LABEL):

    sql_query = f"""

    {get_order_level_cte(year)}

    SELECT

        CASE
            WHEN is_delivery_late = 1 THEN 'Late Delivery'
            ELSE 'On Time'
        END AS delivery_status,

        COUNT(*) AS orders

    FROM order_level

    GROUP BY 1

    """

    return query(sql_query)


def get_delay_reason(year=ALL_YEARS_LABEL):

    where_clause = _year_where(year)

    sql_query = f"""

    WITH order_level AS (
        SELECT
            order_id,
            MAX(is_delivery_late)         AS is_delivery_late,
            MAX(seller_processing_days)   AS seller_processing_days,
            MAX(carrier_transit_days)     AS carrier_transit_days,
            MAX(total_delivery_days)      AS total_delivery_days
        FROM workspace.gold.fact_delivery_performance
        {where_clause}
        GROUP BY order_id
    )

    SELECT

        ROUND(AVG(seller_processing_days), 2) AS seller_processing_days,
        ROUND(AVG(carrier_transit_days), 2)   AS carrier_transit_days,
        ROUND(AVG(total_delivery_days), 2)    AS total_delivery_days

    FROM order_level

    WHERE is_delivery_late = 1

    """

    return query(sql_query).iloc[0]


def get_top_risk_sellers(min_orders: int = 20, limit: int = 15, year=ALL_YEARS_LABEL):

    where_clause = _year_where(year)

    sql_query = f"""

    SELECT

        seller_id,

        COUNT(*) AS total_items,

        ROUND(AVG(is_seller_late) * 100, 2) AS late_rate

    FROM workspace.gold.fact_delivery_performance

    {where_clause}

    GROUP BY seller_id

    HAVING COUNT(*) > {min_orders}

    ORDER BY late_rate DESC

    LIMIT {limit}

    """

    return query(sql_query)


def get_state_risk(year=ALL_YEARS_LABEL):

    sql_query = f"""

    {get_order_level_cte(year)}

    SELECT

        customer_state,

        COUNT(*) AS orders,

        ROUND(AVG(is_delivery_late) * 100, 2) AS late_rate,

        ROUND(AVG(customer_lat), 4) AS lat,
        ROUND(AVG(customer_lng), 4) AS lng

    FROM order_level

    WHERE customer_lat IS NOT NULL
      AND customer_lng IS NOT NULL

    GROUP BY customer_state

    ORDER BY late_rate DESC

    """

    return query(sql_query)


def get_distance_vs_late_rate(year=ALL_YEARS_LABEL):

    year_filter_and = _year_and(year)

    sql_query = f"""

    SELECT

        CASE
            WHEN distance_km < 50   THEN '0-50 km'
            WHEN distance_km < 150  THEN '50-150 km'
            WHEN distance_km < 300  THEN '150-300 km'
            WHEN distance_km < 600  THEN '300-600 km'
            WHEN distance_km < 1000 THEN '600-1000 km'
            ELSE '1000+ km'
        END AS distance_bucket,

        CASE
            WHEN distance_km < 50   THEN 1
            WHEN distance_km < 150  THEN 2
            WHEN distance_km < 300  THEN 3
            WHEN distance_km < 600  THEN 4
            WHEN distance_km < 1000 THEN 5
            ELSE 6
        END AS bucket_order,

        COUNT(*) AS items,

        ROUND(AVG(is_seller_late) * 100, 2) AS late_rate

    FROM workspace.gold.fact_delivery_performance

    WHERE distance_km IS NOT NULL
      {year_filter_and}

    GROUP BY 1, 2

    ORDER BY bucket_order

    """

    return query(sql_query)
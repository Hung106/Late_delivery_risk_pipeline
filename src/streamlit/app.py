import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from queries import (
    ALL_YEARS_LABEL,
    get_available_years,
    get_yearly_summary,
    get_overview,
    get_risk_level_trend,
    get_high_risk_watchlist,
    get_late_rate_trend,
    get_delivery_status,
    get_delay_reason,
    get_top_risk_sellers,
    get_state_risk,
    get_distance_vs_late_rate,
)

st.set_page_config(
    page_title="Hệ thống phân tích rủi ro giao hàng",
    layout="wide"
)


# =====================================================================
def render_keypoints(points: list[str]):
    """Hiển thị các điểm nhấn phân tích (key insights) dưới mỗi biểu đồ."""
    with st.container(border=True):
        st.markdown("**Các điểm nhấn phân tích (Key insights)**")
        for p in points:
            st.markdown(f"- {p}")


def fmt_delta(value, suffix=""):
    """Định dạng delta an toàn: trả về None khi không có kỳ so sánh (NaN)."""
    if value is None or pd.isna(value):
        return None
    return f"{value:+.2f}{suffix}"


st.title("Hệ thống phân tích rủi ro giao hàng")

st.markdown(
"""
Hệ thống giám sát hiệu suất vận hành chuỗi cung ứng, được thiết kế nhằm mục tiêu:
1. **Dự báo và cảnh báo sớm**: Phát hiện các đơn hàng có nguy cơ trễ hạn trước khi sự cố xảy ra để có biện pháp can thiệp.
2. **Đánh giá hiệu suất thực tế**: Theo dõi sát sao tỷ lệ giao hàng đúng hạn và các chỉ số dịch vụ khách hàng, so sánh theo từng năm.
3. **Phân tích nguyên nhân cốt lõi**: Xác định điểm nghẽn trong quy trình (nhà bán hàng, đơn vị vận chuyển, vị trí địa lý) để tối ưu hóa vận hành.
"""
)

# =====================================================================
# THÔNG SỐ CẤU HÌNH (SIDEBAR)
# =====================================================================
st.sidebar.header("Thông số cấu hình hệ thống")

available_years = get_available_years()
year_options = [ALL_YEARS_LABEL] + [str(y) for y in available_years]
default_year_index = 1 if len(year_options) > 1 else 0  # mặc định = năm gần nhất có dữ liệu

selected_year_label = st.sidebar.selectbox(
    "Năm phân tích",
    options=year_options,
    index=default_year_index,
    help="Toàn bộ báo cáo, biểu đồ và danh sách cảnh báo bên dưới sẽ được lọc theo năm này.",
)
selected_year = selected_year_label if selected_year_label == ALL_YEARS_LABEL else int(selected_year_label)

st.sidebar.divider()

late_rate_threshold = st.sidebar.slider(
    "Ngưỡng dung sai: tỷ lệ giao trễ (%)",
    min_value=5,
    max_value=60,
    value=25,
    step=1,
    help="Ngưỡng đánh giá giới hạn chấp nhận được đối với tỷ lệ giao hàng trễ thực tế.",
)

high_risk_threshold = st.sidebar.slider(
    "Ngưỡng cảnh báo: tỷ lệ rủi ro cao (%)",
    min_value=5,
    max_value=50,
    value=15,
    step=1,
    help="Tỷ lệ tối đa cho phép đối với các đơn hàng được hệ thống dự báo có nguy cơ trễ hạn cao.",
)

min_seller_orders = st.sidebar.slider(
    "Kích thước mẫu tối thiểu (nhà bán hàng)",
    min_value=5,
    max_value=100,
    value=20,
    step=5,
    help="Số lượng đơn hàng tối thiểu để hệ thống đưa nhà bán hàng vào diện phân tích rủi ro, nhằm đảm bảo tính đại diện thống kê.",
)

watchlist_limit = st.sidebar.number_input(
    "Giới hạn danh sách cảnh báo vận hành",
    min_value=5,
    max_value=100,
    value=20,
    step=5,
)

st.divider()


# =====================================================================
# PHÂN TÁCH LUỒNG CÔNG VIỆC (TABS)
# =====================================================================
year_caption = "toàn bộ giai đoạn" if selected_year == ALL_YEARS_LABEL else f"năm {selected_year}"

tab_summary, tab_operation, tab_root_cause = st.tabs([
    "Báo cáo tổng quan",
    "Cảnh báo vận hành",
    "Phân tích nguyên nhân cốt lõi"
])

# ---------------------------------------------------------------------
# TAB 1: BÁO CÁO TỔNG QUAN
# ---------------------------------------------------------------------
with tab_summary:
    st.header(f"Báo cáo hiệu suất tổng quan — {year_caption}")
    if selected_year != ALL_YEARS_LABEL:
        st.caption(f"So sánh (YoY) với năm {selected_year - 1}.")
    else:
        st.caption("Đang xem gộp toàn bộ giai đoạn nên không có kỳ so sánh (YoY).")

    kpi = get_overview(selected_year)

    row1 = st.columns(3)
    row1[0].metric("Tổng khối lượng đơn", f"{int(kpi.total_orders):,}")
    row1[1].metric(
        "Tỷ lệ trễ hạn thực tế",
        f"{kpi.late_delivery_rate}%",
        delta=fmt_delta(kpi.late_delivery_rate_delta, "%"),
        delta_color="inverse",
    )
    row1[2].metric(
        "Tỷ lệ đơn rủi ro cao (dự báo)",
        f"{kpi.high_risk_rate}%",
        help="Tỷ trọng đơn hàng được mô hình rủi ro (fact_delivery_risk) gắn nhãn HIGH — chỉ báo sớm, đi trước tỷ lệ trễ thực tế.",
    )

    row2 = st.columns(3)
    row2[0].metric(
        "Chu kỳ giao hàng trung bình (ngày)",
        kpi.avg_delivery_days,
        delta=fmt_delta(kpi.avg_delivery_days_delta),
        delta_color="inverse",
    )
    row2[1].metric(
        "Chỉ số hài lòng (sao)",
        kpi.avg_review_score,
        delta=fmt_delta(kpi.avg_review_score_delta),
        delta_color="normal",
    )
    row2[2].metric("Khoảng cách vận chuyển trung bình", f"{kpi.avg_distance_km} km")

    st.divider()

    col_trend, col_pie = st.columns([2, 1])

    with col_trend:
        st.subheader("Xu hướng tỷ lệ giao trễ theo tháng")
        trend = get_late_rate_trend(selected_year)
        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=trend["period"], y=trend["late_rate"],
                mode="lines+markers", name="Tỷ lệ thực tế",
                line=dict(color="#EF553B", width=2),
            )
        )
        fig_trend.add_hline(
            y=late_rate_threshold, line_dash="dash", line_color="red",
            annotation_text=f"Ngưỡng dung sai ({late_rate_threshold}%)"
        )
        fig_trend.update_layout(xaxis_title="Tháng", yaxis_title="Tỷ lệ (%)", hovermode="x unified")
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_pie:
        st.subheader("Cấu trúc hoàn thành")
        status = get_delivery_status(selected_year)
        status["delivery_status"] = status["delivery_status"].replace({"On Time": "Đúng tiến độ", "Late Delivery": "Trễ hạn"})
        fig_status = px.pie(
            status, names="delivery_status", values="orders",
            color="delivery_status", color_discrete_map={"Đúng tiến độ": "#00CC96", "Trễ hạn": "#EF553B"},
            hole=0.4
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # Keypoints Tab 1
    last_late = trend.iloc[-1]["late_rate"] if len(trend) > 0 else 0
    avg_late = round(trend["late_rate"].mean(), 1) if len(trend) > 0 else 0
    total_orders_status = int(status["orders"].sum())
    late_orders = int(status.loc[status["delivery_status"] == "Trễ hạn", "orders"].sum())
    late_pct = round(late_orders / total_orders_status * 100, 1) if total_orders_status else 0

    insights = [
        f"Tỷ lệ trễ hạn tháng gần nhất đạt **{last_late}%**, so với mức trung bình **{avg_late}%** của {year_caption}.",
        f"Trên tổng **{total_orders_status:,}** đơn hàng, có **{late_pct}%** không đáp ứng cam kết thời gian (SLA) với khách hàng.",
    ]
    if not pd.isna(kpi.late_delivery_rate_delta):
        direction = "tăng, cần rà soát ngay" if kpi.late_delivery_rate_delta > 0 else "giảm, cho thấy cải thiện tích cực"
        insights.append(f"So với năm {selected_year - 1}, tỷ lệ trễ hạn {direction} **{kpi.late_delivery_rate_delta:+.2f} điểm phần trăm** (YoY).")
    insights.append("Khuyến nghị: Chuyển sang phần phân tích nguyên nhân cốt lõi để xác định các yếu tố trọng yếu ảnh hưởng đến hiệu suất.")

    render_keypoints(insights)

# ---------------------------------------------------------------------
# TAB 2: CẢNH BÁO VẬN HÀNH
# ---------------------------------------------------------------------
with tab_operation:
    st.header(f"Danh mục cảnh báo chậm trễ phân bổ (tiền vận hành) — {year_caption}")
    st.caption("Trọng tâm: Cung cấp danh sách các đơn hàng có xác suất trễ hạn cao đang trong tiến trình xử lý để bộ phận CSKH và vận hành can thiệp kịp thời.")

    # Biểu đồ xu hướng rủi ro
    risk_trend = get_risk_level_trend(selected_year)
    fig_risk_trend = go.Figure()

    fig_risk_trend.add_trace(
        go.Scatter(
            x=risk_trend["period"],
            y=risk_trend["high_risk_pct"],
            mode="lines+markers",
            name="Tỷ trọng rủi ro cao",
            line=dict(color="#EF553B", width=2),
        )
    )
    fig_risk_trend.add_trace(
        go.Scatter(
            x=risk_trend["period"],
            y=risk_trend["medium_risk_pct"],
            mode="lines+markers",
            name="Tỷ trọng rủi ro trung bình",
            line=dict(color="#FFA15A", width=2, dash="dot"),
        )
    )
    fig_risk_trend.add_hline(
        y=high_risk_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Ngưỡng kiểm soát ({high_risk_threshold}%)",
        annotation_position="top left",
    )

    fig_risk_trend.update_layout(
        title="Biến động tỷ trọng đơn hàng dự báo rủi ro qua các tháng",
        xaxis_title="Tháng",
        yaxis_title="Tỷ trọng đơn hàng (%)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_risk_trend, use_container_width=True)

    # Keypoints Tab 2
    last_risk = risk_trend.iloc[-1]["high_risk_pct"] if len(risk_trend) > 0 else 0
    compare_idx = -4 if len(risk_trend) >= 4 else 0
    prev_risk = risk_trend.iloc[compare_idx]["high_risk_pct"] if len(risk_trend) > 0 else 0
    risk_delta = round(last_risk - prev_risk, 1)

    risk_status = "vượt qua" if last_risk > high_risk_threshold else "được kiểm soát trong"
    delta_direction = "tăng, đòi hỏi giám sát chặt chẽ" if risk_delta > 0 else ("giảm, cho thấy sự cải thiện quy trình" if risk_delta < 0 else "ổn định")

    render_keypoints([
        f"Tháng gần nhất ghi nhận **{last_risk}%** đơn hàng thuộc nhóm rủi ro cao; hiện trạng này đang {risk_status} ngưỡng cảnh báo thiết lập ({high_risk_threshold}%).",
        f"So với 3 tháng trước, tỷ trọng này biến động **{risk_delta:+.1f}%**; biểu thị xu hướng rủi ro đang {delta_direction}.",
    ])

    st.subheader("Danh sách đơn hàng cần can thiệp khẩn cấp")
    watchlist = get_high_risk_watchlist(limit=watchlist_limit, year=selected_year)

    if watchlist.empty:
        st.info("Hệ thống hiện không ghi nhận đơn hàng nào vượt ngưỡng rủi ro khẩn cấp trong chu trình vận hành hiện tại.")
    else:
        st.dataframe(
            watchlist.rename(columns={
                "order_id": "Mã định danh đơn",
                "seller_id": "Mã nhà bán hàng",
                "customer_state": "Vùng khách hàng",
                "seller_state": "Vùng nhà bán hàng",
                "distance_km": "Khoảng cách (km)",
                "seller_late_rate_pct": "Tỷ lệ trễ lịch sử nhóm bán (%)",
                "avg_processing_days": "Tốc độ xử lý trung bình (ngày)",
                "risk_score": "Chỉ số rủi ro",
                "order_purchase_date": "Thời điểm đặt hàng",
                "order_status": "Trạng thái hiện tại",
            }),
            use_container_width=True,
            hide_index=True,
        )

# ---------------------------------------------------------------------
# TAB 3: PHÂN TÍCH NGUYÊN NHÂN CỐT LÕI (ROOT CAUSE)
# ---------------------------------------------------------------------
with tab_root_cause:
    st.header(f"Đánh giá nguyên nhân và phân bổ điểm nghẽn — {year_caption}")

    st.subheader("1. Phân bổ nguồn gốc sự chậm trễ (nhà bán vs. vận chuyển)")
    st.caption("Trọng tâm: Xác định giai đoạn nào trong quy trình chuỗi cung ứng đóng góp lớn nhất vào tổng thời gian trễ hạn.")
    reason = get_delay_reason(selected_year)
    col_chart, col_total = st.columns([3, 1])
    with col_chart:
        fig_reason = px.bar(
            x=["Xử lý tại kho nhà bán", "Quá trình vận tải"],
            y=[reason.seller_processing_days, reason.carrier_transit_days],
            labels={"x": "Phân đoạn quy trình", "y": "Độ trễ trung bình (ngày)"},
            color=["Xử lý tại kho nhà bán", "Quá trình vận tải"],
            color_discrete_sequence=["#636EFA", "#FFA15A"],
        )
        fig_reason.update_layout(showlegend=False)
        st.plotly_chart(fig_reason, use_container_width=True)
    with col_total:
        st.metric("Tổng thời gian giao (nhóm trễ)", f"{reason.total_delivery_days} ngày")

    dominant_stage = "xử lý tại kho nhà bán" if reason.seller_processing_days > reason.carrier_transit_days else "quá trình vận tải"
    render_keypoints([
        f"Giai đoạn **{dominant_stage}** đang là nút thắt chính yếu trong quy trình xử lý các đơn hàng thất bại về SLA.",
        f"Thời gian lưu trú tại kho nhà bán đạt **{reason.seller_processing_days} ngày**, trong khi thời gian lưu chuyển trên đường là **{reason.carrier_transit_days} ngày**."
    ])

    st.divider()

    st.subheader("2. Ma trận đánh giá năng lực nhà bán hàng")
    st.caption(f"Trọng tâm: Khoanh vùng các đối tác cung cấp có rủi ro cao để áp dụng chính sách chế tài hoặc tái đào tạo (yêu cầu ngưỡng mẫu: >{min_seller_orders} đơn).")
    seller = get_top_risk_sellers(min_orders=min_seller_orders, year=selected_year)

    if seller.empty:
        st.info("Không có nhà bán hàng nào đạt ngưỡng mẫu tối thiểu trong giai đoạn được chọn.")
    else:
        fig_seller = px.scatter(
            seller, x="total_items", y="late_rate", size="total_items", color="late_rate",
            color_continuous_scale="Reds", hover_name="seller_id",
            labels={"total_items": "Khối lượng giao dịch", "late_rate": "Tỷ lệ vi phạm SLA (%)"},
        )
        fig_seller.add_hline(y=late_rate_threshold, line_dash="dash", line_color="red", annotation_text="Ngưỡng kiểm soát")
        st.plotly_chart(fig_seller, use_container_width=True)

        worst_seller = seller.loc[seller["late_rate"].idxmax()]
        n_over_threshold = int((seller["late_rate"] > late_rate_threshold).sum())
        render_keypoints([
            f"Ghi nhận **{n_over_threshold} đối tác** vượt ngưỡng vi phạm cho phép ({late_rate_threshold}%). Đề xuất bộ phận Vendor Management có biện pháp rà soát.",
            f"Đối tác mã định danh **{worst_seller['seller_id'][:8]}...** có tỷ suất vi phạm nghiêm trọng nhất, đạt **{worst_seller['late_rate']}%** trên tổng {worst_seller['total_items']} giao dịch."
        ])

    st.divider()

    st.subheader("3. Tương quan địa lý và khoảng cách vận chuyển")
    col_map, col_dist = st.columns(2)

    state = get_state_risk(selected_year)
    with col_map:
        if not state.empty and not state["lat"].isna().all():
            fig_state_map = px.scatter_geo(
                state, lat="lat", lon="lng", size="orders", color="late_rate",
                color_continuous_scale="Reds", hover_name="customer_state",
                title="Tỷ lệ vi phạm SLA phân bổ theo vùng (bubble size = quy mô đơn)",
                scope="south america",
            )
            fig_state_map.update_geos(center=dict(lat=-14, lon=-51), projection_scale=3.5, showcountries=True)
            st.plotly_chart(fig_state_map, use_container_width=True)
        else:
            st.info("Không có dữ liệu tọa độ khách hàng cho giai đoạn được chọn.")

    dist = get_distance_vs_late_rate(selected_year)
    with col_dist:
        fig_dist = px.bar(
            dist, x="distance_bucket", y="late_rate", text="items",
            title="Sự phụ thuộc của tỷ lệ vi phạm vào khoảng cách địa lý",
            labels={"distance_bucket": "Phân khúc khoảng cách", "late_rate": "Tỷ lệ vi phạm SLA (%)"},
        )
        fig_dist.update_traces(texttemplate="%{text:,} đơn", textposition="outside")
        st.plotly_chart(fig_dist, use_container_width=True)

    if len(dist) > 0 and len(state) > 0:
        farthest = dist.iloc[-1]
        worst_state = state.iloc[0]
        render_keypoints([
            f"Phân khúc khoảng cách xa nhất ({farthest['distance_bucket']}) ghi nhận tỷ lệ vi phạm **{farthest['late_rate']}%**. Khuyến nghị: Điều chỉnh tăng thời gian dự kiến giao hàng (EDD) cho phân khúc này trên hệ thống front-end.",
            f"Khu vực **{worst_state['customer_state']}** đang là vùng có hiệu suất hậu cần kém nhất (**{worst_state['late_rate']}%**). Đề xuất làm việc với đơn vị vận chuyển tại địa phương này."
        ])
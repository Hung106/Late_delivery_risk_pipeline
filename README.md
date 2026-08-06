# 🚚 Olist Late Delivery Risk Pipeline

## Overview

Dự án xây dựng một **End-to-End Data Engineering Pipeline** trên bộ dữ liệu thương mại điện tử Olist nhằm phân tích rủi ro giao hàng trễ.

Hệ thống xử lý dữ liệu từ nguồn OLTP, xây dựng Data Lake và Data Warehouse theo mô hình **Medallion Architecture**, tự động hóa pipeline bằng **Apache Airflow** và cung cấp dashboard phân tích bằng **Streamlit**.


## Architecture

```
Olist Dataset
      |
      v
PostgreSQL
      |
      v
Airflow Pipeline
      |
      v
Bronze Layer
      |
      v
Silver Layer
      |
      v
Gold Layer
      |
      v
Streamlit Dashboard
```


## Tech Stack

| Category | Technologies |
|---|---|
| Programming | Python, SQL |
| Processing | PySpark, Spark SQL |
| Database | PostgreSQL |
| Storage | Parquet |
| Orchestration | Apache Airflow |
| Visualization | Streamlit, Plotly |
| Environment | Docker |


## Project Structure

```
Late_delivery_risk_pipeline

├── airflow
├── src
│   ├── extract
│   ├── transform
│   ├── quality
│   └── streamlit
├── docker
├── data
├── notebooks
├── docker-compose.yml
├── requirements.txt
└── README.md
```


# Getting Started


## 1. Clone repository

```bash
git clone <repository-url>

cd Late_delivery_risk_pipeline
```


## 2. Install dependencies

```bash
pip install -r requirements.txt
```


## 3. Start services

```bash
docker compose up -d
```


## 4. Run pipeline
Thêm dữ liệu từ mục data/source vào PostgreSQL
Pipeline được quản lý bởi Apache Airflow. Airflow server local: http://localhost:8080

Sau khi khởi động Airflow, trigger DAG để thực hiện:

- Data extraction
- Data transformation
- Data loading


## 5. Run Dashboard

```bash
streamlit run src/streamlit/app.py
```
Dashboard local: http://localhost:8501

# Outcome

- Xây dựng pipeline xử lý dữ liệu end-to-end.
- Áp dụng Medallion Architecture cho Data Lake.
- Xây dựng Data Warehouse phục vụ phân tích delivery risk.
- Tự động hóa workflow bằng Apache Airflow.
- Phát triển dashboard hỗ trợ theo dõi hiệu suất giao hàng.


# 📚 Documentation

Chi tiết về kiến trúc, data model, pipeline workflow và business logic được trình bày trong thư mục:

```
docs/
```

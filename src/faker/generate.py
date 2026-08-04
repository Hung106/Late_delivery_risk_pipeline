import uuid
import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker


fake = Faker()

from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://postgres:postgres@localhost:5433/olist_oltp_db",
    future=True,
    pool_pre_ping=True
)


# ==========================================================
# Helper
# ==========================================================

def generate_id():
    return str(uuid.uuid4()).replace("-", "")[:32]


def get_existing_ids(table, column, limit=None):

    sql = f"""
    SELECT {column}
    FROM {table}
    """

    if limit:
        sql += f"""
        LIMIT {limit}
        """

    df = pd.read_sql(
        sql,
        engine
    )

    return df[column].tolist()



# ==========================================================
# Generate Customers
# ==========================================================

def generate_customers(n=100):

    rows = []

    for _ in range(n):

        rows.append(
            {
                "customer_id": generate_id(),
                "customer_unique_id": generate_id(),
                "customer_zip_code_prefix": random.randint(10000,99999),
                "customer_city": fake.city(),
                "customer_state": random.choice(
                    [
                        "SP",
                        "RJ",
                        "MG",
                        "PR",
                        "RS"
                    ]
                )
            }
        )

    return pd.DataFrame(rows)



# ==========================================================
# Generate Sellers
# ==========================================================

def generate_sellers(n=10):

    rows=[]

    for _ in range(n):

        rows.append(
            {
                "seller_id": generate_id(),
                "seller_zip_code_prefix": random.randint(10000,99999),
                "seller_city": fake.city(),
                "seller_state": random.choice(
                    [
                        "SP",
                        "RJ",
                        "MG"
                    ]
                )
            }
        )

    return pd.DataFrame(rows)



# ==========================================================
# Generate Orders
# ==========================================================

def generate_orders(customers):

    rows=[]

    now=datetime.now()


    for customer_id in customers["customer_id"]:


        purchase_time = (
            now
            -
            timedelta(
                days=random.randint(0,2),
                hours=random.randint(0,23)
            )
        )


        status=random.choice(
            [
                "delivered",
                "shipped",
                "processing"
            ]
        )


        estimated = (
            purchase_time
            +
            timedelta(
                days=random.randint(5,10)
            )
        )


        if status=="delivered":

            carrier_date = (
                purchase_time
                +
                timedelta(days=random.randint(1,3))
            )

            customer_date = (
                carrier_date
                +
                timedelta(days=random.randint(1,5))
            )

        else:

            carrier_date=None
            customer_date=None



        rows.append(
            {
                "order_id": generate_id(),

                "customer_id": customer_id,

                "order_status": status,

                "order_purchase_timestamp": purchase_time,

                "order_approved_at":
                    purchase_time + timedelta(hours=2),

                "order_delivered_carrier_date":
                    carrier_date,

                "order_delivered_customer_date":
                    customer_date,

                "order_estimated_delivery_date":
                    estimated
            }
        )


    return pd.DataFrame(rows)



# ==========================================================
# Generate Order Items
# ==========================================================

def generate_order_items(
    orders,
    sellers,
    products
):

    rows=[]


    for _,order in orders.iterrows():

        item_count=random.randint(1,3)


        for i in range(1,item_count+1):

            rows.append(
                {
                    "order_id":
                        order.order_id,

                    "order_item_id":
                        i,

                    "product_id":
                        random.choice(products),

                    "seller_id":
                        random.choice(sellers),

                    "shipping_limit_date":
                        order.order_purchase_timestamp
                        +
                        timedelta(days=3),

                    "price":
                        round(random.uniform(20,500),2),

                    "freight_value":
                        round(random.uniform(5,80),2)
                }
            )


    return pd.DataFrame(rows)



# ==========================================================
# Payments
# ==========================================================

def generate_payments(orders):

    rows=[]


    for order_id in orders.order_id:

        rows.append(
            {
                "order_id": order_id,

                "payment_sequential":1,

                "payment_type":
                    random.choice(
                        [
                            "credit_card",
                            "boleto",
                            "voucher"
                        ]
                    ),

                "payment_installments":
                    random.randint(1,5),

                "payment_value":
                    round(
                        random.uniform(50,500),
                        2
                    )
            }
        )


    return pd.DataFrame(rows)



# ==========================================================
# Reviews
# ==========================================================

def generate_reviews(orders):

    rows=[]


    for order_id in orders.order_id:

        rows.append(
            {
                "review_id":generate_id(),

                "order_id":order_id,

                "review_score":
                    random.randint(1,5),

                "review_comment_title":
                    None,

                "review_comment_message":
                    None,

                "review_creation_date":
                    datetime.now(),

                "review_answer_timestamp":
                    datetime.now()
            }
        )


    return pd.DataFrame(rows)


def insert_dataframe(df, table):

    if len(df) == 0:
        return

    df.to_sql(
        table,
        engine,
        if_exists="append",
        index=False
    )

    print(f"{table}: inserted {len(df)} rows")


# ==========================================================
# Main Batch
# ==========================================================

def main():

    print("=" * 60)
    print("Starting incremental fake batch...")
    print("=" * 60)

    customers = generate_customers(100)
    insert_dataframe(
        customers,
        "customers"
    )

    sellers = generate_sellers(10)
    insert_dataframe(
        sellers,
        "sellers"
    )

    products = get_existing_ids(
        "products",
        "product_id"
    )

    if not products:
        raise Exception("No products found.")

    orders = generate_orders(customers)
    insert_dataframe(
        orders,
        "orders"
    )

    items = generate_order_items(
        orders,
        sellers.seller_id.tolist(),
        products
    )
    insert_dataframe(
        items,
        "order_items"
    )

    payments = generate_payments(orders)
    insert_dataframe(
        payments,
        "order_payments"
    )

    reviews = generate_reviews(orders)
    insert_dataframe(
        reviews,
        "order_reviews"
    )

    print("=" * 60)
    print("Incremental fake batch completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
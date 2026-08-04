import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from logger import get_logger


logger = get_logger(__name__)


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_CONTAINER_PORT")
DB_NAME = os.getenv("POSTGRES_DB")


DATABASE_URL = (
    f"postgresql://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}"
    f"/{DB_NAME}"
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)



def get_engine() -> Engine:

    return engine



def test_connection():

    logger.info("Testing PostgreSQL connection...")

    try:

        with engine.connect() as conn:

            conn.execute(
                text("SELECT 1")
            )

        logger.info(
            "PostgreSQL connection successful."
        )

    except Exception:

        logger.exception(
            "Cannot connect to PostgreSQL."
        )

        raise




def read_table(
    table_name: str,
    load_type: str = "full",
    watermark_column: str | None = None,
    last_watermark: str | None = None
) -> pd.DataFrame:


    logger.info(
        f"Reading table [{table_name}] | "
        f"Load type: {load_type}"
    )


    if load_type == "full":


        query = text(
            f"""
            SELECT *
            FROM {table_name}
            """
        )

        params = None



    elif load_type == "incremental":


        if not last_watermark:


            logger.info(
                f"No watermark found for {table_name}. "
                "Running initial load."
            )


            query = text(
                f"""
                SELECT *
                FROM {table_name}
                """
            )

            params = None



        else:

            if table_name == "order_items":


                query = text(
                    """
                    SELECT oi.*

                    FROM order_items oi

                    JOIN orders o
                    ON oi.order_id = o.order_id

                    WHERE o.order_purchase_timestamp
                    > :last_watermark
                    """
                )


                params = {
                    "last_watermark": last_watermark
                }



            else:


                if not watermark_column:

                    raise ValueError(
                        f"Missing watermark column "
                        f"for {table_name}"
                    )


                query = text(
                    f"""
                    SELECT *
                    FROM {table_name}

                    WHERE {watermark_column}
                    > :last_watermark
                    """
                )


                params = {
                    "last_watermark": last_watermark
                }



    else:


        raise ValueError(
            f"Unsupported load type: {load_type}"
        )




    df = pd.read_sql(
        query,
        engine,
        params=params
    )


    logger.info(
        f"{table_name}: {len(df)} rows loaded."
    )


    return df




def read_query(
    sql: str,
    params: dict | None = None
) -> pd.DataFrame:


    logger.info(
        "Executing SQL query..."
    )


    df = pd.read_sql(
        text(sql),
        engine,
        params=params
    )


    logger.info(
        f"{len(df)} rows returned."
    )


    return df



def execute_query(
    sql: str,
    params: dict | None = None
):


    with engine.begin() as conn:

        conn.execute(
            text(sql),
            params or {}
        )



def fetch_one(
    sql: str,
    params: dict | None = None
):


    with engine.connect() as conn:


        result = conn.execute(
            text(sql),
            params or {}
        )


        row = result.mappings().first()


    return row



def fetch_all(
    sql: str,
    params: dict | None = None
):


    with engine.connect() as conn:


        result = conn.execute(
            text(sql),
            params or {}
        )


        rows = result.mappings().all()


    return rows




def table_exists(
    table_name: str
) -> bool:


    sql = """
    SELECT EXISTS (

        SELECT 1

        FROM information_schema.tables

        WHERE table_schema='public'

        AND table_name=:table_name

    )
    """


    result = fetch_one(
        sql,
        {
            "table_name": table_name
        }
    )


    return result["exists"]



def get_row_count(
    table_name: str
):


    sql = f"""
    SELECT COUNT(*)
    FROM {table_name}
    """


    row = fetch_one(sql)


    return row["count"]


def dispose_engine():

    logger.info(
        "Closing PostgreSQL Engine..."
    )

    engine.dispose()
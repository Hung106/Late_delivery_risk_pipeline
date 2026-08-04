from datetime import datetime

import pandas as pd
from sqlalchemy import text

from logger import get_logger
from postgres import get_engine


logger = get_logger(__name__)

engine = get_engine()


def get_table_config(table_name: str):

    query = text("""
        SELECT
            table_name,
            load_type,
            watermark_column,
            last_watermark
        FROM pipeline_metadata
        WHERE table_name = :table_name
    """)

    with engine.connect() as conn:

        result = conn.execute(
            query,
            {
                "table_name": table_name
            }
        ).mappings().first()

    return result



def start_pipeline_run(
    batch_id,
    table_name,
    load_type
):

    query = text("""
        INSERT INTO public.pipeline_run_history
        (
            batch_id,
            table_name,
            load_type,
            start_time,
            status
        )
        VALUES
        (
            :batch_id,
            :table_name,
            :load_type,
            :start_time,
            'RUNNING'
        )
        RETURNING run_id
    """)

    with engine.begin() as conn:

        run_id = conn.execute(
            query,
            {
                "batch_id": batch_id,
                "table_name": table_name,
                "load_type": load_type,
                "start_time": datetime.now()
            }
        ).scalar()

    return run_id



def finish_pipeline_run(
    run_id,
    rows_extracted
):

    query = text("""
        UPDATE public.pipeline_run_history
        SET
            end_time = :end_time,
            rows_extracted = :rows,
            status = 'SUCCESS'
        WHERE run_id = :run_id
    """)

    with engine.begin() as conn:

        conn.execute(
            query,
            {
                "end_time": datetime.now(),
                "rows": rows_extracted,
                "run_id": run_id
            }
        )


def fail_pipeline_run(
    run_id,
    error_message
):

    query = text("""
        UPDATE public.pipeline_run_history
        SET
            end_time = :end_time,
            status = 'FAILED',
            error_message = :error_message
        WHERE run_id = :run_id
    """)

    with engine.begin() as conn:

        conn.execute(
            query,
            {
                "end_time": datetime.now(),
                "error_message": error_message,
                "run_id": run_id
            }
        )



def update_watermark(
    table_name,
    batch_id,
    watermark
):

    query = text("""
        UPDATE pipeline_metadata
        SET
            last_watermark = :watermark,
            last_batch_id = :batch_id,
            last_run_time = :run_time,
            updated_at = CURRENT_TIMESTAMP
        WHERE table_name = :table_name
    """)

    with engine.begin() as conn:

        conn.execute(
            query,
            {
                "watermark": watermark,
                "batch_id": batch_id,
                "run_time": datetime.now(),
                "table_name": table_name
            }
        )
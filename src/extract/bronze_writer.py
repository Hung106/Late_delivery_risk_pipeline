from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from logger import get_logger

logger = get_logger(__name__)


def write_bronze(
    df: pd.DataFrame,
    table_name: str,
    bronze_path: Path,
    batch_id: str,
    ingestion_date: str
):
    """
    Write dataframe to Bronze layer as Parquet.
    Compatible with Databricks/Spark.
    """

    partition_path = (
        bronze_path
        / table_name
        / f"ingestion_date={ingestion_date}"
    )

    partition_path.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        partition_path
        / f"{table_name}_{batch_id}.parquet"
    )

    table = pa.Table.from_pandas(
        df,
        preserve_index=False
    )

    pq.write_table(
        table,
        output_file,
        compression="snappy",
        coerce_timestamps="us",
        allow_truncated_timestamps=True
    )

    logger.info(f"{table_name} saved to {output_file}")

    return output_file
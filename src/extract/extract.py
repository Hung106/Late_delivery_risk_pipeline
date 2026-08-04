import sys
from datetime import datetime

from logger import get_logger
from postgres import test_connection, read_table
from bronze_writer import write_bronze
from config import get_enabled_tables, get_bronze_path
from metadata import (
    start_pipeline_run,
    finish_pipeline_run,
    fail_pipeline_run,
)
from databricks_uploader import upload_file_to_volume

logger = get_logger(__name__)


def main():
    # Nhận batch_id từ Airflow, nếu chạy thủ công thì sinh mới
    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
    else:
        batch_id = datetime.now().strftime("%Y%m%dT%H%M%S")

    ingestion_date = datetime.now().strftime("%Y-%m-%d")

    logger.info("=" * 80)
    logger.info(f"Starting Extract Pipeline | Batch ID: {batch_id}")
    logger.info("=" * 80)

    # ------------------------------------------------------------------
    # Test PostgreSQL connection
    # ------------------------------------------------------------------
    try:
        test_connection()
        logger.info("PostgreSQL connection successful.")
    except Exception:
        logger.exception("Cannot connect to PostgreSQL.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Load configuration
    # ------------------------------------------------------------------
    try:
        bronze_path = get_bronze_path()
        enabled_tables = get_enabled_tables()

        logger.info(f"Bronze path: {bronze_path}")
        logger.info(f"Enabled tables: {list(enabled_tables.keys())}")

    except Exception:
        logger.exception("Cannot load extract.yaml")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Process each table
    # ------------------------------------------------------------------
    for table_name, table_config in enabled_tables.items():

        load_type = table_config.get("load_type", "full")

        logger.info("-" * 80)
        logger.info(f"Processing table: {table_name}")
        logger.info(f"Load type: {load_type}")

        run_id = start_pipeline_run(
            batch_id=batch_id,
            table_name=table_name,
            load_type=load_type,
        )

        try:

            # ----------------------------------------------------------
            # Extract
            # ----------------------------------------------------------
            logger.info(f"Reading table: {table_name}")

            df = read_table(table_name)

            rows_extracted = len(df)

            logger.info(f"Rows extracted: {rows_extracted}")

            if rows_extracted == 0:
                logger.warning(f"{table_name} contains 0 rows.")

            # ----------------------------------------------------------
            # Write Bronze
            # ----------------------------------------------------------
            logger.info("Writing parquet to local Bronze...")

            output_file = write_bronze(
                df=df,
                table_name=table_name,
                bronze_path=bronze_path,
                batch_id=batch_id,
                ingestion_date=ingestion_date,
            )

            logger.info(f"Output file: {output_file}")

            if not output_file.exists():
                raise FileNotFoundError(
                    f"Parquet file was not created: {output_file}"
                )

            logger.info("Parquet file created successfully.")

            # ----------------------------------------------------------
            # Upload to Databricks Volume
            # ----------------------------------------------------------
            databricks_volume_path = (
                "/Volumes/workspace/bronze/bronze_olist"
            )

            logger.info(
                f"Uploading {output_file.name} "
                f"to {databricks_volume_path}"
            )

            upload_file_to_volume(
                output_file,
                databricks_volume_path,
            )

            logger.info("Upload completed successfully.")

            # ----------------------------------------------------------
            # Metadata
            # ----------------------------------------------------------
            finish_pipeline_run(
                run_id=run_id,
                rows_extracted=rows_extracted,
            )

            logger.info(f"{table_name} completed successfully.")

        except Exception as e:

            logger.exception(
                f"Failed processing table: {table_name}"
            )

            fail_pipeline_run(
                run_id=run_id,
                error_message=str(e),
            )

            # Dừng pipeline ngay khi có lỗi
            raise

    logger.info("=" * 80)
    logger.info(f"Pipeline finished successfully. Batch ID: {batch_id}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
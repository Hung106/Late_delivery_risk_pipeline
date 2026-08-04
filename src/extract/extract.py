import sys
from datetime import datetime

from logger import get_logger
from postgres import test_connection, read_table
from bronze_writer import write_bronze
from config import get_enabled_tables, get_bronze_path
from metadata import (
    get_table_config,
    start_pipeline_run,
    finish_pipeline_run,
    fail_pipeline_run,
    update_watermark,
)
from databricks_uploader import upload_file_to_volume

logger = get_logger(__name__)


def main():

    # ==========================================================
    # Batch ID
    # ==========================================================

    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
    else:
        batch_id = datetime.now().strftime("%Y%m%dT%H%M%S")

    ingestion_date = datetime.now().strftime("%Y-%m-%d")

    logger.info("=" * 80)
    logger.info(f"Starting Extract Pipeline | Batch ID: {batch_id}")
    logger.info("=" * 80)

    # ==========================================================
    # Test PostgreSQL Connection
    # ==========================================================

    try:

        test_connection()

    except Exception:

        logger.exception("Cannot connect to PostgreSQL.")

        sys.exit(1)

    # ==========================================================
    # Load Config
    # ==========================================================

    try:

        bronze_path = get_bronze_path()

        enabled_tables = get_enabled_tables()

        logger.info(f"Bronze path: {bronze_path}")

        logger.info(
            f"Enabled tables: {list(enabled_tables.keys())}"
        )

    except Exception:

        logger.exception(
            "Cannot load extract.yaml"
        )

        sys.exit(1)

    # ==========================================================
    # Process Tables
    # ==========================================================

    for table_name in enabled_tables.keys():

        logger.info("-" * 80)
        logger.info(f"Processing table: {table_name}")

        # ------------------------------------------------------
        # Metadata
        # ------------------------------------------------------

        table_meta = get_table_config(table_name)

        if table_meta is None:

            raise Exception(
                f"Metadata not found for table: {table_name}"
            )

        load_type = table_meta["load_type"]

        watermark_column = table_meta["watermark_column"]

        last_watermark = table_meta["last_watermark"]

        logger.info(f"Load type: {load_type}")

        logger.info(
            f"Last watermark: {last_watermark}"
        )

        run_id = start_pipeline_run(
            batch_id=batch_id,
            table_name=table_name,
            load_type=load_type,
        )

        try:

            # ==================================================
            # Extract
            # ==================================================

            df = read_table(
                table_name=table_name,
                load_type=load_type,
                watermark_column=watermark_column,
                last_watermark=last_watermark,
            )

            rows_extracted = len(df)

            logger.info(
                f"Rows extracted: {rows_extracted}"
            )

            if rows_extracted == 0:

                logger.warning(
                    f"No new rows found for {table_name}"
                )

            # ==================================================
            # Write Bronze
            # ==================================================

            output_file = write_bronze(
                df=df,
                table_name=table_name,
                bronze_path=bronze_path,
                batch_id=batch_id,
                ingestion_date=ingestion_date,
            )

            if not output_file.exists():

                raise FileNotFoundError(
                    f"Parquet file was not created: {output_file}"
                )

            logger.info(
                f"Bronze file created: {output_file.name}"
            )

            # ==================================================
            # Upload Databricks Volume
            # ==================================================

            upload_file_to_volume(
                output_file,
                "/Volumes/workspace/bronze/bronze_olist"
            )

            logger.info(
                "Upload completed successfully."
            )

            # ==================================================
            # Update Watermark
            # ==================================================

            if (
                load_type == "incremental"
                and rows_extracted > 0
            ):

                if table_name == "orders":

                    new_watermark = df[
                        "order_purchase_timestamp"
                    ].max()

                elif table_name == "order_reviews":

                    new_watermark = df[
                        "review_creation_date"
                    ].max()

                elif table_name == "order_items":

                    # order_items dùng chung watermark
                    # với orders
                    new_watermark = last_watermark

                else:

                    new_watermark = df[
                        watermark_column
                    ].max()

                update_watermark(
                    table_name=table_name,
                    batch_id=batch_id,
                    watermark=new_watermark,
                )

                logger.info(
                    f"Watermark updated: {new_watermark}"
                )

            # ==================================================
            # Finish Metadata
            # ==================================================

            finish_pipeline_run(
                run_id=run_id,
                rows_extracted=rows_extracted,
            )

            logger.info(
                f"{table_name} completed successfully."
            )

        except Exception as e:

            logger.exception(
                f"Failed processing table: {table_name}"
            )

            fail_pipeline_run(
                run_id=run_id,
                error_message=str(e),
            )

            raise

    logger.info("=" * 80)

    logger.info(
        f"Pipeline finished successfully. Batch ID: {batch_id}"
    )

    logger.info("=" * 80)


if __name__ == "__main__":
    main()
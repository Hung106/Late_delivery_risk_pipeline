from pathlib import Path

import yaml

from logger import get_logger

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]

CONFIG_FILE = BASE_DIR / "config" / "extract.yaml"


def load_config():

    logger.info(f"Loading config: {CONFIG_FILE}")

    if not CONFIG_FILE.exists():

        raise FileNotFoundError(
            f"Config file not found: {CONFIG_FILE}"
        )

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        config = yaml.safe_load(f)

    logger.info("Config loaded successfully.")

    return config



def get_bronze_path():

    config = load_config()

    return (
        BASE_DIR
        / config["bronze"]["output_path"]
    )



def get_tables():

    config = load_config()

    return config["tables"]



def get_enabled_tables():

    tables = get_tables()

    enabled_tables = {}

    for table_name, table_config in tables.items():

        if table_config.get(
            "enabled",
            True
        ):

            enabled_tables[
                table_name
            ] = table_config

    return enabled_tables
from pathlib import Path
from databricks.sdk import WorkspaceClient
from logger import get_logger

logger = get_logger(__name__)

def upload_file_to_volume(local_file_path: Path, volume_dir: str):
    """
    Tự động upload file local lên Databricks Volume.
    Databricks SDK sẽ tự động đọc DATABRICKS_HOST và DATABRICKS_TOKEN từ file .env.
    """
    logger.info(f"Bắt đầu upload file lên Databricks: {local_file_path.name}")
    
    w = WorkspaceClient()
    
    destination_path = f"{volume_dir}/{local_file_path.name}"
    
    try:
        with open(local_file_path, "rb") as f:
            w.files.upload(destination_path, f, overwrite=True)
            
        logger.info(f"Upload thành công lên Databricks Volume: {destination_path}")
    except Exception as e:
        logger.exception(f"Lỗi khi upload file {local_file_path.name} lên Databricks.")
        raise
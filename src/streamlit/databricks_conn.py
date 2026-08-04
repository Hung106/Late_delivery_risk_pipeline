import os
from dotenv import load_dotenv
from databricks import sql


load_dotenv()


def get_connection():

    hostname = os.getenv("DATABRICKS_HOST")
    http_path = os.getenv("DATABRICKS_HTTP_PATH")
    token = os.getenv("DATABRICKS_TOKEN")

    print("HOST:", hostname)
    print("HTTP:", http_path)
    print("TOKEN:", token[:10] if token else None)

    return sql.connect(
        server_hostname=hostname,
        http_path=http_path,
        access_token=token
    )
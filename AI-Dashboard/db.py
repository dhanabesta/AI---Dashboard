import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

# Load database settings from .env
load_dotenv()

def get_asset_data():
    connection = None

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "asset_management")
        )

        query = "SELECT * FROM asset_master"

        df = pd.read_sql(query, connection)

        return df

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
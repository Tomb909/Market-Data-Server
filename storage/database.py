import sqlite3
import os
import pandas as pd

DB_PATH= os.path.join(os.path.dirname(__file__), "yields.db") 

def GetConnection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def InitDB():
    conn = GetConnection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yields (
            date TEXT,
            country TEXT,
            instrument TEXT,
            maturity REAL,
            yield REAL,
            PRIMARY KEY (date, country, maturity)
        )
    """)

    conn.commit()
    conn.close()

def UpsertYields(df: pd.DataFrame, conn):
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR REPLACE INTO yields
            (date, country, instrument, maturity, yield)
        VALUES
            (:date, :country, :instrument, :maturity, :yield)
    """, df.to_dict(orient="records"))
    conn.commit()

if __name__ == "__main__":
    InitDB()
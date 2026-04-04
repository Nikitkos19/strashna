import json
import sqlite3
from pathlib import Path


def get_connection(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_mc_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def build_result_payload(result):
    return {
        "detectedMcIds": result["detectedMcIds"],
        "shouldSplit": result["shouldSplit"],
        "drafts": result["drafts"],
    }


def save_analysis_run(db_path, source_mc_id, description, result):
    payload = build_result_payload(result)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analysis_runs (source_mc_id, description, result_json)
            VALUES (?, ?, ?)
            """,
            (
                source_mc_id,
                description,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        return cursor.lastrowid

import sqlite3
from pathlib import Path

DB_NAME = "emart24.db"
SCHEMA_FILE = "schema.sql"


def create_database():
    schema_path = Path(SCHEMA_FILE)

    if not schema_path.exists():
        print(f"오류: {SCHEMA_FILE} 파일을 찾을 수 없습니다.")
        return

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(schema_path, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    print(f"{DB_NAME} 데이터베이스 생성 완료!")


if __name__ == "__main__":
    create_database()
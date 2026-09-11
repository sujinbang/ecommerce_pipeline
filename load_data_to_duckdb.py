import os
from pathlib import Path

import duckdb

# 실행 위치와 무관하게 동작하도록 스크립트 기준 경로를 사용한다.
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = Path(os.environ.get("RAW_DATA_DIR", BASE_DIR / "raw_data"))
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", BASE_DIR / "ecommerce.duckdb"))

def load_data():
    print(f"DuckDB 데이터베이스 연결 중... ({DUCKDB_PATH})")
    con = duckdb.connect(str(DUCKDB_PATH))

    print("1. orders.csv 데이터를 raw_orders 테이블로 적재...")
    # csv 파일의 모든 컬럼을 문자열(VARCHAR)로 강제 지정하여 읽어옵니다.
    # (결측치나 이상한 포맷이 있어도 일단 다 문자열로 밀어넣고, 나중에 dbt에서 정제하기 위함)
    con.execute("""
        CREATE OR REPLACE TABLE raw_orders AS
        SELECT * FROM read_csv(?, all_varchar=1)
    """, [str(RAW_DATA_DIR / "orders.csv")])

    print("2. user_logs.jsonl 데이터를 raw_user_logs 테이블로 적재...")
    # jsonl 파일을 읽어옵니다. DuckDB는 JSON 구조를 알아서 파싱합니다.
    con.execute("""
        CREATE OR REPLACE TABLE raw_user_logs AS
        SELECT * FROM read_json_auto(?)
    """, [str(RAW_DATA_DIR / "user_logs.jsonl")])
    
    print("\n✅ 데이터 적재 완료! 생성된 테이블 목록:")
    print(con.execute("SHOW TABLES").fetchdf())
    
    con.close()

if __name__ == "__main__":
    load_data()

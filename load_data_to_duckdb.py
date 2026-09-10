import duckdb

def load_data():
    print("DuckDB 데이터베이스 연결 중... (ecommerce.duckdb 생성)")
    con = duckdb.connect('ecommerce.duckdb')
    
    print("1. orders.csv 데이터를 raw_orders 테이블로 적재...")
    # csv 파일의 모든 컬럼을 문자열(VARCHAR)로 강제 지정하여 읽어옵니다. 
    # (결측치나 이상한 포맷이 있어도 일단 다 문자열로 밀어넣고, 나중에 dbt에서 정제하기 위함)
    con.execute("""
        CREATE OR REPLACE TABLE raw_orders AS 
        SELECT * FROM read_csv('raw_data/orders.csv', all_varchar=1)
    """)
    
    print("2. user_logs.jsonl 데이터를 raw_user_logs 테이블로 적재...")
    # jsonl 파일을 읽어옵니다. DuckDB는 JSON 구조를 알아서 파싱합니다.
    con.execute("""
        CREATE OR REPLACE TABLE raw_user_logs AS 
        SELECT * FROM read_json_auto('raw_data/user_logs.jsonl')
    """)
    
    print("\n✅ 데이터 적재 완료! 생성된 테이블 목록:")
    print(con.execute("SHOW TABLES").fetchdf())
    
    con.close()

if __name__ == "__main__":
    load_data()

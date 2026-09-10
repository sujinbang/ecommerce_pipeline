import duckdb
import pandas as pd

# DuckDB 파일에 연결 (읽기 전용 모드로 열면 다른 프로그램과 동시에 열 수 있습니다)
con = duckdb.connect('ecommerce.duckdb', read_only=True)

def run_query(sql):
    print(f"\n--- 실행할 쿼리 ---\n{sql}\n-------------------")
    # 결과를 판다스 데이터프레임으로 예쁘게 출력
    df = con.execute(sql).fetchdf()
    print(df)
    print("\n")

# 1. 만들어진 테이블(뷰) 목록 확인
run_query("SHOW TABLES;")

# 2. Airflow가 최종적으로 만든 일별 매출 마트 데이터 확인 (상위 10개)
run_query("""
    SELECT * 
    FROM mart_daily_revenue 
    ORDER BY order_date DESC 
    LIMIT 10;
""")

# 3. 데이터가 잘 정제되었는지 Staging 테이블 확인
run_query("""
    SELECT * 
    FROM stg_orders 
    WHERE amount = 0 -- 결측치나 마이너스가 0으로 잘 바뀌었는지 확인
    LIMIT 5;
""")

con.close()

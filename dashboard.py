import os
from pathlib import Path

import streamlit as st
import duckdb
import plotly.express as px

BASE_DIR = Path(__file__).resolve().parent
DUCKDB_PATH = Path(os.environ.get("DUCKDB_PATH", BASE_DIR / "ecommerce.duckdb"))

# 페이지 기본 설정
st.set_page_config(page_title="이커머스 주간 현황", layout="wide")

st.title("🛒 이커머스 매출 대시보드 (DuckDB 연동)")
st.write("Airflow와 dbt가 만들어낸 `mart_daily_revenue` 테이블을 시각화한 결과입니다.")

# DuckDB에서 데이터 불러오기 (캐싱을 통해 속도 최적화)
@st.cache_data
def load_data():
    # 읽기 전용으로 열어서 Airflow와 충돌 방지
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_daily_revenue ORDER BY order_date").fetchdf()
    con.close()
    return df

df = load_data()

if not df.empty:
    # 1. 상단 요약 지표 (가장 최근 일자 기준)
    latest_date = df['order_date'].max()
    recent_data = df[df['order_date'] == latest_date]
    
    total_rev = recent_data['total_revenue'].sum()
    total_ord = recent_data['total_orders'].sum()

    st.subheader(f"최근 현황 (기준일: {latest_date.strftime('%Y-%m-%d')})")
    col1, col2 = st.columns(2)
    col1.metric(label="어제 총 매출액", value=f"₩{total_rev:,.0f}")
    col2.metric(label="어제 총 주문 건수", value=f"{total_ord} 건")
    st.divider()

    # 2. 메인 차트 (일자별/기기별 매출 추이)
    st.subheader("📈 일자별 매출 추이")
    
    # Plotly를 이용한 누적 막대 차트 생성
    fig = px.bar(
        df, 
        x='order_date', 
        y='total_revenue', 
        color='device',
        title="기기별(Device) 일일 매출액",
        labels={'order_date': '결제 일자', 'total_revenue': '매출액 (원)', 'device': '접속 기기'},
        barmode='stack'
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. 원본 데이터 표 노출
    st.subheader("📊 상세 마트(Mart) 데이터")
    st.dataframe(df, use_container_width=True)
else:
    st.warning("데이터가 없습니다. Airflow 파이프라인이 정상적으로 돌았는지 확인해주세요.")

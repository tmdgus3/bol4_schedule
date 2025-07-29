import streamlit as st
import pandas as pd
import datetime
import folium
from streamlit_folium import st_folium
from io import StringIO

# --- CSV 파일 로딩 ---
@st.cache_data
def load_schedule():
    return pd.read_csv("schedule.csv")

# --- 날짜 파싱 및 분리 ---
def parse_schedule(df):
    df["날짜"] = pd.to_datetime(df["날짜"])
    df_online = df[df["내용"].str.contains("온라인")].copy()
    df_offline = df[~df["내용"].str.contains("온라인")].copy()
    return df_online, df_offline

# --- 일정 렌더링 함수 ---
def render_schedule(df, title):
    if df.empty:
        st.markdown(f"#### {title}\n- 해당 날짜에 일정이 없습니다.")
        return
    st.markdown(f"#### {title}")
    for _, row in df.iterrows():
        st.markdown(f"""
**⬤ {row['위치']}**  
&nbsp;&nbsp;&nbsp;&nbsp;{row['도로명주소']}  
&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}  
🕒 {row['시간']}  
📝 {row['내용']}  
        """)

# --- 지도 표시 ---
def render_map(df):
    if df.empty:
        return
    m = folium.Map(location=[36.5, 127.8], zoom_start=7)
    colors = ["red", "blue", "green", "purple", "orange"]
    for i, (_, row) in enumerate(df.iterrows()):
        folium.Marker(
            location=None,  # 주소를 기반으로 좌표 변환이 필요한 경우 geopy 등 필요
            tooltip=row["위치"],
            popup=f"{row['내용']}\n{row['도로명주소']}",
            icon=folium.Icon(color=colors[i % len(colors)])
        ).add_to(m)
    st_folium(m, width=1200, height=600)

# --- 메인 앱 ---
st.set_page_config(layout="wide")
st.title("🎵 볼빨간사춘기 일정 보기")

# 전체 스케줄 불러오기
df_all = load_schedule()
df_online, df_offline = parse_schedule(df_all)

# 날짜 목록 추출 및 달력 표시
available_dates = sorted(df_all["날짜"].dt.date.unique())
selected_date = st.date_input("날짜 선택", value=datetime.date.today())

# 선택된 날짜의 일정 필터링
df_sel_online = df_online[df_online["날짜"].dt.date == selected_date]
df_sel_offline = df_offline[df_offline["날짜"].dt.date == selected_date]

# 일정 및 지도 표시
render_schedule(df_sel_offline, "오프라인 일정")
render_schedule(df_sel_online, "온라인 일정")
render_map(df_sel_offline)

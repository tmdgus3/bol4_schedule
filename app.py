import streamlit as st
import pandas as pd
import datetime
import folium
from streamlit_folium import st_folium
import os

# --- 기본 설정 ---
st.set_page_config(page_title="일정 지도", layout="wide")

# --- 파일 경로 및 데이터 불러오기 ---
DATA_PATH = "schedule.csv"
df = pd.read_csv(DATA_PATH)

# 날짜 형식 변환
df["날짜"] = pd.to_datetime(df["날짜"]).dt.date

# 온라인/오프라인 구분
online_df = df[df["내용"].str.contains("온라인")]
offline_df = df[~df["내용"].str.contains("온라인")]

# 현재 선택된 날짜 (전체 달력 표시)
today = datetime.date.today()
selected_date = st.date_input("날짜 선택", value=today)

# --- 상단: 일정 표시 ---
st.markdown("## 📅 일정 보기")

selected_online = online_df[online_df["날짜"] == selected_date]
selected_offline = offline_df[offline_df["날짜"] == selected_date]

if selected_online.empty and selected_offline.empty:
    st.info("해당 날짜에는 일정이 없습니다.")
else:
    if not selected_offline.empty:
        st.markdown("### ⬤ 오프라인 일정")
        for _, row in selected_offline.iterrows():
            st.markdown(
                f"""**{row['내용']}**  
⬤ {row['위치']}  
&nbsp;&nbsp;&nbsp;&nbsp;{row['도로명주소']}  
&nbsp;&nbsp;&nbsp;&nbsp;{row['메모'] if pd.notna(row['메모']) else ''}  
"""
            )

    if not selected_online.empty:
        st.markdown("### 🌐 온라인 일정")
        for _, row in selected_online.iterrows():
            st.markdown(
                f"""**{row['내용']}**  
🌐 온라인 일정  
&nbsp;&nbsp;&nbsp;&nbsp;{row['메모'] if pd.notna(row['메모']) else ''}  
"""
            )

# --- 지도 표시 ---
st.markdown("## 📍 지도 보기")
if not offline_df.empty:
    # 지도 중심은 대한민국 중앙 좌표 (위도, 경도)
    map_center = [36.5, 127.5]
    m = folium.Map(location=map_center, zoom_start=7)

    # 핀 색상 리스트
    color_list = [
        "red", "blue", "green", "orange", "purple",
        "darkred", "cadetblue", "darkgreen", "black", "pink"
    ]

    for i, (_, row) in enumerate(offline_df.iterrows()):
        if pd.notna(row["도로명주소"]):
            # 각 장소에 대해 마커 추가
            tooltip = f"{row['내용']} - {row['위치']}"
            popup = f"{row['위치']}<br>{row['도로명주소']}<br>{row['메모'] if pd.notna(row['메모']) else ''}"
            folium.Marker(
                location=None,  # Geocoding 필요 시 수정
                tooltip=tooltip,
                popup=popup,
                icon=folium.Icon(color=color_list[i % len(color_list)])
            ).add_to(m)

    # 지도 출력
    st_data = st_folium(m, width=1200, height=600)
else:
    st.warning("오프라인 일정이 없어 지도를 표시할 수 없습니다.")

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# 파일 경로
CSV_FILE = "schedule.csv"

# --- 타이틀 및 최종 수정일 표시 ---
st.title("볼빨간사춘기 스케줄 관리")
if os.path.exists(CSV_FILE):
    last_modified = datetime.fromtimestamp(os.path.getmtime(CSV_FILE)).strftime("%Y-%m-%d %H:%M")
    st.markdown(f"<p style='font-size: 12px; color: gray;'>📅 최종 수정일: {last_modified}</p>", unsafe_allow_html=True)

# --- CSV 로딩 ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
else:
    df = pd.DataFrame(columns=["날짜", "시간", "주소", "내용"])

# --- 일정 추가 ---
st.subheader("📝 일정 추가")
with st.form("add_form"):
    date = st.date_input("날짜")
    time = st.time_input("시간")
    address = st.text_input("주소")
    content = st.text_input("내용")
    submitted = st.form_submit_button("일정 추가")
    if submitted and address and content:
        new_row = pd.DataFrame([[str(date), str(time), address, content]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        st.success("일정이 추가되었습니다!")

# --- 일정 테이블 보기 ---
st.subheader("📋 전체 일정")
if df.empty:
    st.info("현재 저장된 일정이 없습니다.")
else:
    st.dataframe(df)

# --- 지도 표시 ---
st.subheader("📍 일정 위치 보기")
geolocator = Nominatim(user_agent="bol4-schedule")
map_center = [36.5, 127.5]  # 대한민국 중심

m = folium.Map(location=map_center, zoom_start=7)

for _, row in df.iterrows():
    try:
        location = geolocator.geocode(row["주소"])
        if location:
            folium.Marker(
                [location.latitude, location.longitude],
                popup=f"{row['날짜']} {row['시간']} - {row['내용']}"
            ).add_to(m)
    except:
        continue

st_folium(m, height=500)

# --- 관리자 모드 ---
st.subheader("🔒 관리자 모드 (일정 삭제)")
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

edit_options = [f"{i}: {row['날짜']} {row['시간']} {row['내용']}" for i, row in df.iterrows()]
selected = st.selectbox("삭제할 일정을 선택하세요", [""] + edit_options)

if selected:
    idx = int(selected.split(":")[0])
    if st.button("선택한 일정 삭제"):
        df = df.drop(idx).reset_index(drop=True)
        df.to_csv(CSV_FILE, index=False)
        st.success("일정이 삭제되었습니다.")

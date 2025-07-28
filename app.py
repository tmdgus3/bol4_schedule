import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import datetime
import pytz
import os

# 페이지 설정
st.set_page_config(page_title="볼빨간사춘기 스케줄 관리", layout="wide")
st.title("📅 볼빨간사춘기 스케줄 관리")

# 경로 및 로딩
DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="bol4_schedule_app")

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["날짜", "시간", "내용", "메모", "위치", "도로명주소"])

df = load_data()

# 최종 수정일시 표시 (KST 기준)
if os.path.exists(DATA_PATH):
    kst = pytz.timezone("Asia/Seoul")
    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(DATA_PATH), tz=kst)
    st.caption(f"📌 최종 수정일: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 온라인/오프라인 일정 구분 (도로명주소가 없으면 온라인)
online_df = df[df["도로명주소"].isna() | (df["도로명주소"].str.strip() == "")]
offline_df = df[~df.index.isin(online_df.index)]

# -----------------------------------
# 💻 온라인 일정
# -----------------------------------
st.subheader("💻 온라인 일정")
if not online_df.empty:
    for i, row in online_df.iterrows():
        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")
        if pd.notna(row["메모"]) and row["메모"].strip() != "":
            st.caption(f"📝 {row['메모']}")
        if pd.notna(row["위치"]):
            st.button(f"📺 {row['위치']}", key=f"online_show_{i}", disabled=True)
else:
    st.info("온라인 일정이 없습니다.")

# -----------------------------------
# 📍 오프라인 일정
# -----------------------------------
st.subheader("📍 오프라인 일정")
if not offline_df.empty:
    for i, row in offline_df.iterrows():
        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")
        if pd.notna(row["메모"]) and row["메모"].strip() != "":
            st.caption(f"📝 {row['메모']}")
        if pd.notna(row["위치"]):
            if st.button(f"📋 {row['위치']}", key=f"show_address_{i}"):
                st.markdown(f"➡️ `{row['도로명주소']}`")
else:
    st.info("오프라인 일정이 없습니다.")

# -----------------------------------
# 🗺️ 지도 표시
# -----------------------------------
st.subheader("🗺️ 오프라인 위치 보기")
m = folium.Map(location=[36.5, 127.8], zoom_start=7)
m.fit_bounds([[33.0, 124.5], [38.7, 131.2]])

for _, row in offline_df.iterrows():
    if pd.notna(row["도로명주소"]):
        try:
            location = geolocator.geocode(row["도로명주소"])
            if location:
                folium.Marker(
                    location=[location.latitude, location.longitude],
                    popup=row["내용"],
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)
        except:
            continue

st_folium(m, width=800, height=450)

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

# 데이터 경로 및 Geocoder 설정
DATA_PATH = "schedule.csv"
geolocator = Nominatim(user_agent="bol4_schedule_app")

# 색상 정의 (오프라인 일정용 마커 색상)
pin_colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]

# 데이터 로드 함수
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["날짜", "시간", "내용", "메모", "위치", "도로명주소"])

df = load_data()

# 최종 수정일시 (KST 기준)
if os.path.exists(DATA_PATH):
    kst = pytz.timezone("Asia/Seoul")
    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(DATA_PATH), tz=kst)
    st.caption(f"📌 최종 수정일: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 온라인/오프라인 일정 구분
online_df = df[df["도로명주소"].isna() | (df["도로명주소"].str.strip() == "")]
offline_df = df[~df.index.isin(online_df.index)]

# -----------------------------------
# 📆 날짜 선택 필터
# -----------------------------------
st.subheader("📆 날짜별 일정 보기")
selected_date = st.date_input("날짜를 선택하세요", value=datetime.date.today())
selected_str = selected_date.strftime("%Y-%m-%d")

selected_online = online_df[online_df["날짜"] == selected_str]
selected_offline = offline_df[offline_df["날짜"] == selected_str]

# -----------------------------------
# 💻 온라인 일정
# -----------------------------------
st.subheader("💻 온라인 일정")
if not selected_online.empty:
    for i, row in selected_online.iterrows():
        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")
        if pd.notna(row["위치"]):
            st.markdown(f"⬤ {row['위치']}")
        if pd.notna(row["메모"]) and row["메모"].strip() != "":
            st.markdown(f"\n&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}")
else:
    st.info("온라인 일정이 없습니다.")

# -----------------------------------
# 📍 오프라인 일정
# -----------------------------------
st.subheader("📍 오프라인 일정")
if not selected_offline.empty:
    for i, row in selected_offline.iterrows():
        color = pin_colors[i % len(pin_colors)]

        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")

        # 위치
        st.markdown(f"⬤ <span style='color:{color}'>{row['위치']}</span>", unsafe_allow_html=True)

        # 도로명주소 (회색, 들여쓰기)
        if pd.notna(row["도로명주소"]):
            st.markdown(f"<span style='color:gray;'>&nbsp;&nbsp;&nbsp;&nbsp;{row['도로명주소']}</span>", unsafe_allow_html=True)

        # 메모 (있으면)
        if pd.notna(row["메모"]) and row["메모"].strip() != "":
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}", unsafe_allow_html=True)
else:
    st.info("오프라인 일정이 없습니다.")

# -----------------------------------
# 🗺️ 지도 표시 (대한민국 남한 범위 제한)
# -----------------------------------
st.subheader("🗺️ 오프라인 위치 보기")
m = folium.Map(location=[36.5, 127.8], zoom_start=7)
m.fit_bounds([[33.0, 124.5], [38.7, 131.2]])  # 대한민국 본토 범위

for i, row in offline_df.iterrows():
    color = pin_colors[i % len(pin_colors)]
    if pd.notna(row["도로명주소"]):
        try:
            location = geolocator.geocode(row["도로명주소"])
            if location:
                folium.Marker(
                    location=[location.latitude, location.longitude],
                    popup=row["내용"],
                    icon=folium.Icon(color=color, icon="info-sign")
                ).add_to(m)
        except:
            continue

st_folium(m, width=800, height=450)

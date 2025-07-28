import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from datetime import datetime
import time

# CSV 파일 경로
CSV_PATH = "schedule.csv"

# 페이지 기본 설정
st.set_page_config(page_title="볼빨간사춘기 스케줄 관리", layout="centered")

st.title("📅 볼빨간사춘기 스케줄 관리")

# 마지막 수정 시간
def get_modified_time(path):
    t = time.localtime(os.path.getmtime(path))
    return time.strftime("%Y-%m-%d %H:%M", t)

st.markdown(f"<p style='font-size:12px; color:gray; text-align:right'>최종 수정: {get_modified_time(CSV_PATH)}</p>", unsafe_allow_html=True)

# 데이터 로딩
@st.cache_data
def load_schedule():
    return pd.read_csv(CSV_PATH)

df = load_schedule()

# 온라인/오프라인 구분
online_df = df[df["온라인/오프라인"] == "온라인"]
offline_df = df[df["온라인/오프라인"] == "오프라인"]

# 온라인 일정
st.header("🖥 온라인 일정")
if online_df.empty:
    st.info("온라인 일정이 없습니다.")
else:
    st.dataframe(online_df.drop(columns=["위치", "온라인/오프라인"]))

# 오프라인 일정
st.header("📍 오프라인 일정 (지도 포함)")
if offline_df.empty:
    st.info("오프라인 일정이 없습니다.")
else:
    st.dataframe(offline_df.drop(columns=["온라인/오프라인"]))
    
    geolocator = Nominatim(user_agent="bol4_app")
    map_data = []

    for _, row in offline_df.iterrows():
        if pd.notna(row["위치"]) and row["위치"].strip():
            try:
                loc = geolocator.geocode(row["위치"])
                if loc:
                    map_data.append({"lat": loc.latitude, "lon": loc.longitude})
            except:
                continue
    
    if map_data:
        st.map(pd.DataFrame(map_data))
    else:
        st.warning("유효한 주소가 없어 지도를 표시할 수 없습니다.")

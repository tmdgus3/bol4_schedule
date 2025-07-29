import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import datetime
import os

# 📁 데이터 경로
DATA_PATH = "schedule.csv"

# 📍 색상 설정
pin_colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]

# 📄 데이터 로드
@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=["날짜", "시간", "내용", "메모", "위치", "도로명주소"])
    df = pd.read_csv(DATA_PATH)
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
    return df

df = load_data()
online_df = df[df["도로명주소"].isna() | (df["도로명주소"].str.strip() == "")]
offline_df = df[~df.index.isin(online_df.index)]

# 📅 Streamlit 시작
st.set_page_config(page_title="볼빨간사춘기 스케줄 관리", layout="wide")
st.title("📅 볼빨간사춘기 스케줄 관리")

# 최종 수정일
if os.path.exists(DATA_PATH):
    modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(DATA_PATH))
    st.caption(f"📌 최종 수정일: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 📆 달력 위젯 (일정 있는 날짜만 선택 가능)
available_dates = sorted(df["날짜"].unique())
selected_date = st.date_input(
    "날짜 선택", value=datetime.date.today(), min_value=min(available_dates),
    max_value=max(available_dates), label_visibility="collapsed"
)

# 📌 세부 일정
st.markdown(f"## 📌 {selected_date.strftime('%Y-%m-%d')} 일정")

selected_online = online_df[online_df["날짜"] == selected_date]
selected_offline = offline_df[offline_df["날짜"] == selected_date]

# 🏟️ 오프라인 일정
st.subheader("🏟️ 오프라인 일정")
if not selected_offline.empty:
    for i, row in selected_offline.iterrows():
        color = pin_colors[i % len(pin_colors)]
        st.markdown(f"**{row['시간']} - {row['내용']}**")
        st.markdown(f"⬤ <span style='color:{color}'>{row['위치']}</span>", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['도로명주소']}", unsafe_allow_html=True)
        if pd.notna(row["메모"]) and row["메모"].strip():
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}", unsafe_allow_html=True)
else:
    st.info("해당 날짜에 오프라인 일정이 없습니다.")

# 💻 온라인 일정
st.subheader("💻 온라인 일정")
if not selected_online.empty:
    for i, row in selected_online.iterrows():
        st.markdown(f"**{row['시간']} - {row['내용']}**")
        st.markdown(f"⬤ {row['위치']}")
        if pd.notna(row["메모"]) and row["메모"].strip():
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}")
else:
    st.info("해당 날짜에 온라인 일정이 없습니다.")

# 🗺️ 지도 (디폴트 중앙 위치, 줌만 설정)
st.subheader("🗺️ 오프라인 위치 보기")
geolocator = Nominatim(user_agent="bol4_schedule_app")
m = folium.Map(location=[36.5, 127.8], zoom_start=7)

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

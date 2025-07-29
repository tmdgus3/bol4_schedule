import streamlit as st
import pandas as pd
import datetime
import calendar
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

# 페이지 설정
st.set_page_config(page_title="📆 볼빨간사춘기 일정", layout="centered")
st.markdown("## 📅 볼빨간사춘기 전체 달력")

# CSV 불러오기
df = pd.read_csv("schedule.csv")
df["날짜"] = pd.to_datetime(df["날짜"]).dt.date

# 세션 상태 초기화
if "year" not in st.session_state:
    st.session_state.year = datetime.date.today().year
if "month" not in st.session_state:
    st.session_state.month = datetime.date.today().month
if "clicked_date" not in st.session_state:
    st.session_state.clicked_date = None

# 월/년 이동 버튼
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ 이전달"):
        if st.session_state.month == 1:
            st.session_state.month = 12
            st.session_state.year -= 1
        else:
            st.session_state.month -= 1

with col3:
    if st.button("다음달 ➡️"):
        if st.session_state.month == 12:
            st.session_state.month = 1
            st.session_state.year += 1
        else:
            st.session_state.month += 1

with col2:
    st.markdown(f"<h4 style='text-align:center'>{st.session_state.year}년 {st.session_state.month}월</h4>", unsafe_allow_html=True)

# 달력 그리기
cal = calendar.Calendar()
month_days = list(cal.itermonthdates(st.session_state.year, st.session_state.month))

day_labels = ["일", "월", "화", "수", "목", "금", "토"]
cols = st.columns(7)
for i, label in enumerate(day_labels):
    cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{label}</div>", unsafe_allow_html=True)

for week_start in range(0, len(month_days), 7):
    cols = st.columns(7)
    for i in range(7):
        day = month_days[week_start + i]
        style = "width:100%; height:60px; text-align:center; border-radius:6px; border:1px solid #ccc; margin:2px; font-size:16px;"
        day_events = df[df["날짜"] == day]
        if day.month != st.session_state.month:
            cols[i].markdown(" ")
        else:
            with cols[i].form(key=f"form_{day}"):
                btn = st.form_submit_button(
                    label=f"{day.day}\n{'📌' if not day_events.empty else ''}"
                )
                if btn:
                    st.session_state.clicked_date = day

# 클릭된 날짜 일정 보기
if st.session_state.clicked_date:
    clicked_day = st.session_state.clicked_date
    st.markdown(f"### 📍 {clicked_day} 일정")

    df_sel = df[df["날짜"] == clicked_day]
    df_online = df_sel[df_sel["내용"].str.contains("온라인", na=False)]
    df_offline = df_sel[~df_sel["내용"].str.contains("온라인", na=False)]

    if not df_online.empty:
        st.markdown("#### 💻 온라인 일정")
        for _, row in df_online.iterrows():
            st.markdown(f"- {row['시간']} {row['내용']}")

    if not df_offline.empty:
        st.markdown("#### 🏟️ 오프라인 일정")
        for _, row in df_offline.iterrows():
            st.markdown(f"- {row['시간']} {row['내용']} ({row['위치']})")

        # 지도 표시
        geolocator = Nominatim(user_agent="bol4_schedule")
        m = folium.Map(location=[36.5, 127.9], zoom_start=7)
        for _, row in df_offline.iterrows():
            loc = geolocator.geocode(row["도로명주소"])
            if loc:
                folium.Marker(
                    location=[loc.latitude, loc.longitude],
                    popup=row["위치"],
                    tooltip=row["내용"]
                ).add_to(m)
        st_folium(m, width=1100, height=600)
else:
    st.info("날짜를 눌러 일정을 확인하세요.")

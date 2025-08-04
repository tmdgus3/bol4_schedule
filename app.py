# app.py

import streamlit as st
import pandas as pd
import datetime
import calendar
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="centered", page_title="📆 BOL4 일정 캘린더")

# Load data
@st.cache_data
def load_schedule():
    df = pd.read_csv("schedule.csv")
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
    return df

df = load_schedule()

# 현재 연도와 월
today = datetime.date.today()
year, month = today.year, today.month

# 달력 출력
def render_calendar(df, year, month):
    st.markdown(f"<h2 style='text-align: center;'>📅 {year}년 {month}월</h2>", unsafe_allow_html=True)
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)
    colnames = ['일', '월', '화', '수', '목', '금', '토']

    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{colnames[i]}</div>", unsafe_allow_html=True)

    for week in month_days:
        cols = st.columns(7)
        for i, date in enumerate(week):
            with cols[i]:
                if date.month != month:
                    st.markdown(" ")
                else:
                    events_exist = not df[df["날짜"] == date].empty
                    button_label = f"**{date.day}**" if events_exist else str(date.day)
                    if st.button(button_label, key=str(date)):
                        st.session_state["selected_date"] = date

# 일정 출력
def show_schedule(df, selected_date):
    df_day = df[df["날짜"] == selected_date]
    if df_day.empty:
        st.info("이 날에는 등록된 일정이 없습니다.")
        return

    df_online = df_day[df_day["내용"].str.contains("온라인", na=False)]
    df_offline = df_day[~df_day["내용"].str.contains("온라인", na=False)]

    if not df_offline.empty:
        st.subheader("📍 오프라인 일정")
        for _, row in df_offline.iterrows():
            st.markdown(f"""
            **🗓 {row['내용']}**

            위치: `{row['위치']}`  
            {row['메모'] if pd.notna(row['메모']) and row['메모'] else ''}
            """)
        show_map(df_offline)

    if not df_online.empty:
        st.subheader("💻 온라인 일정")
        for _, row in df_online.iterrows():
            st.markdown(f"""
            **🗓 {row['내용']}**

            {row['메모'] if pd.notna(row['메모']) and row['메모'] else ''}
            """)

# 지도 출력
def show_map(df_offline):
    if df_offline.empty:
        return
    geolocator = Nominatim(user_agent="calendar-app")
    m = folium.Map(location=[36.5, 127.9], zoom_start=7)
    for _, row in df_offline.iterrows():
        try:
            location = geolocator.geocode(row["도로명주소"])
            if location:
                folium.Marker(
                    location=[location.latitude, location.longitude],
                    popup=row["위치"],
                    icon=folium.Icon(color="blue")
                ).add_to(m)
        except:
            continue
    st_folium(m, width=800, height=500)

# 앱 실행
st.title("🎤 볼사 일정 달력")
render_calendar(df, year, month)

if "selected_date" in st.session_state:
    st.markdown("---")
    st.markdown(f"### 📌 {st.session_state['selected_date']} 일정")
    show_schedule(df, st.session_state["selected_date"])

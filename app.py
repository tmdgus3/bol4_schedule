import streamlit as st
import pandas as pd
import datetime
import calendar

st.set_page_config(page_title="📆 볼빨간사춘기 일정", layout="centered")
st.markdown("## 📅 볼빨간사춘기 전체 달력")

# CSV 로드
df = pd.read_csv("schedule.csv")
df["날짜"] = pd.to_datetime(df["날짜"]).dt.date

# 한 달 달력 만들기
today = datetime.date.today()
year = today.year
month = today.month
cal = calendar.Calendar()
month_days = list(cal.itermonthdates(year, month))

# 클릭 감지용 변수
clicked_date = None

# 달력 출력
cols = st.columns(7)
day_labels = ["일", "월", "화", "수", "목", "금", "토"]
for i, label in enumerate(day_labels):
    cols[i].markdown(f"**{label}**")

for week_start in range(0, len(month_days), 7):
    cols = st.columns(7)
    for i in range(7):
        day = month_days[week_start + i]
        if day.month != month:
            cols[i].markdown(" ")
        else:
            day_events = df[df["날짜"] == day]
            if not day_events.empty:
                if cols[i].button(f"{day.day}\n📌"):
                    clicked_date = day
            else:
                if cols[i].button(str(day.day)):
                    clicked_date = day

# 클릭된 날짜 일정 표시
if clicked_date:
    st.markdown(f"### 📍 {clicked_date} 일정")
    df_sel = df[df["날짜"] == clicked_date]

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

        # 지도
        from geopy.geocoders import Nominatim
        from streamlit_folium import st_folium
        import folium

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

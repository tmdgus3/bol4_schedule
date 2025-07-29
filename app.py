from datetime import datetime
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="볼빨간사춘기 일정 보기", layout="centered")
st.markdown("## 🎵 볼빨간사춘기 일정 보기")

# Load data
DATA_PATH = "schedule.csv"
df = pd.read_csv(DATA_PATH)
df['날짜'] = pd.to_datetime(df['날짜']).dt.date

# Display full calendar
events = []
for i, row in df.iterrows():
    events.append({
        "title": row['내용'],
        "start": str(row['날짜']),
        "end": str(row['날짜']),
    })

calendar_result = calendar(
    events=events,
    options={
        "initialView": "dayGridMonth",
        "locale": "ko",
        "height": 600,
        "headerToolbar": {
            "start": "prev,next today",
            "center": "title",
            "end": ""
        }
    },
)

# ✅ 날짜 클릭이 아닌 "이벤트 클릭" 기준으로 처리
selected_event = calendar_result.get("event")
if selected_event and selected_event.get("start"):
    selected_date = datetime.strptime(selected_event["start"][:10], "%Y-%m-%d").date()
    st.markdown(f"### 📅 {selected_date} 일정")

    df_sel = df[df["날짜"] == selected_date]

    if "내용" in df_sel.columns:
        df_sel_online = df_sel[df_sel["내용"].str.contains("온라인", na=False)]
        df_sel_offline = df_sel[~df_sel["내용"].str.contains("온라인", na=False)]
    else:
        st.error("⚠️ '내용' 컬럼이 schedule.csv에 없습니다.")
        st.stop()

    # 오프라인 일정
    st.markdown("#### 🏟️ 오프라인 일정")
    if not df_sel_offline.empty:
        for _, row in df_sel_offline.iterrows():
            st.markdown(f"- **{row['위치']}**  \n"
                        f"  {row['도로명주소']}  \n"
                        f"  {row['시간']}  \n"
                        f"  {row['내용']}")
        
        # 지도
        geolocator = Nominatim(user_agent="schedule_app")
        m = folium.Map(location=[36.5, 127.9], zoom_start=7)
        for _, row in df_sel_offline.iterrows():
            location = geolocator.geocode(row["도로명주소"])
            if location:
                folium.Marker(
                    location=[location.latitude, location.longitude],
                    popup=row["위치"],
                    tooltip=row["내용"]
                ).add_to(m)

        st_folium(m, width=1200, height=600)
    else:
        st.markdown("- 해당 날짜에 오프라인 일정이 없습니다.")

    # 온라인 일정
    st.markdown("#### 💻 온라인 일정")
    if not df_sel_online.empty:
        for _, row in df_sel_online.iterrows():
            st.markdown(f"- {row['시간']}  \n  {row['내용']}")
    else:
        st.markdown("- 해당 날짜에 온라인 일정이 없습니다.")
else:
    st.info("📅 캘린더에서 일정을 클릭하면 세부 내용을 볼 수 있어요!")

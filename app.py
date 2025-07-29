import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim

st.set_page_config(page_title="볼빨간사춘기 일정 보기", layout="centered")

st.markdown("## 🎵 볼빨간사춘기 일정 보기")

# CSV 불러오기
DATA_PATH = "schedule.csv"
df = pd.read_csv(DATA_PATH)
df['날짜'] = pd.to_datetime(df['날짜']).dt.date

# 캘린더 표시
events = []
for i, row in df.iterrows():
    date = row['날짜']
    title = row['내용']
    events.append({
        "title": title,
        "start": str(date),
        "end": str(date)
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
    custom_css="""
    .fc-toolbar-title { font-size: 24px; font-weight: bold; }
    """
)

# 선택된 날짜 확인
selected_date_str = calendar_result.get("date")
if selected_date_str:
    selected_date = datetime.strptime(selected_date_str[:10], "%Y-%m-%d").date()
    st.markdown(f"### 📅 {selected_date} 일정")

    # 선택 날짜 필터링
    df_sel = df[df["날짜"] == selected_date]

    # 오프라인 / 온라인 구분
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
        
        # 지도 표시
        geolocator = Nominatim(user_agent="schedule_app")
        m = folium.Map(location=[36.5, 127.9], zoom_start=7)  # 대한민국 중심
        
        for _, row in df_sel_offline.iterrows():
            address = row["도로명주소"]
            location = geolocator.geocode(address)
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
    st.info("달력에서 날짜를 클릭하면 해당 날짜의 일정이 표시됩니다.")

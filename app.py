import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# CSV 파일 경로
CSV_PATH = "schedule.csv"

# 페이지 설정
st.set_page_config(page_title="볼빨간사춘기 일정 보기", layout="centered")
st.title("🎵 볼빨간사춘기 일정 보기")

# 일정 데이터 로딩
@st.cache_data
def load_schedule():
    df = pd.read_csv(CSV_PATH)
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
    df["시간"] = df["시간"].fillna("")
    df["메모"] = df["메모"].fillna("")
    return df

df = load_schedule()

# 전체 달력 보여주기
selected_date = st.date_input("날짜 선택", value=None)

# 날짜에 따른 일정 필터링
df_sel = df[df["날짜"] == selected_date] if selected_date else pd.DataFrame()
df_sel_online = df_sel[df_sel["내용"].str.contains("온라인")]
df_sel_offline = df_sel[~df_sel["내용"].str.contains("온라인")]

# 오프라인 일정 출력
if not df_sel_offline.empty:
    st.subheader("📍 오프라인 일정")
    for _, row in df_sel_offline.iterrows():
        st.markdown(f"**● {row['위치']}**")
        st.markdown(f"{row['도로명주소']}")
        if row['시간']:
            st.markdown(f"🕒 {row['시간']}")
        st.markdown(f"📝 {row['내용']}")
        st.markdown("---")

# 온라인 일정 출력
st.subheader("💻 온라인 일정")
if not df_sel_online.empty:
    for _, row in df_sel_online.iterrows():
        if row['시간']:
            st.markdown(f"🕒 {row['시간']}")
        st.markdown(f"📝 {row['내용']}")
        st.markdown("---")
else:
    st.markdown("- 해당 날짜에 일정이 없습니다.")

# 지도 출력 함수
def render_map(df):
    geolocator = Nominatim(user_agent="schedule_app")
    if not df.empty:
        first_addr = df.iloc[0]["도로명주소"]
        try:
            loc = geolocator.geocode(first_addr)
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=13)
        except:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7)
    else:
        return

    for _, row in df.iterrows():
        try:
            loc = geolocator.geocode(row["도로명주소"])
            if loc:
                folium.Marker(
                    [loc.latitude, loc.longitude],
                    tooltip=row["내용"],
                    popup=row["위치"]
                ).add_to(m)
        except:
            continue

    st_folium(m, width=1200, height=600)

# 오프라인 일정이 있을 경우에만 지도 출력
if not df_sel_offline.empty:
    render_map(df_sel_offline)

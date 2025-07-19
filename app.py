import streamlit as st
import pandas as pd
import datetime
from streamlit_folium import st_folium
import folium
from geopy.geocoders import Nominatim

# 기본 지도 위치: 대한민국 중심
DEFAULT_LAT = 36.5
DEFAULT_LON = 127.5

st.set_page_config(layout="wide")
st.title("📅 일정 캘린더 + 지도")

# CSV 파일 경로
SCHEDULE_CSV = "schedules.csv"

# CSV 파일 로드
if "df" not in st.session_state:
    try:
        st.session_state.df = pd.read_csv(SCHEDULE_CSV)
        st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"])
    except:
        st.session_state.df = pd.DataFrame(columns=["Date", "Time", "Title", "Memo", "Location"])

# 관리자 사이드바
with st.sidebar:
    st.markdown("🔐 **관리자 모드**")
    password = st.text_input("비밀번호", type="password")
    is_admin = password == "1234"  # 원하는 비밀번호로 설정

# 일정 추가/수정
st.subheader("✏️ 일정 추가 / 수정")
with st.form("event_form"):
    today = datetime.date.today()
    date = st.date_input("날짜", today)
    time = st.time_input("시간", datetime.time(18, 0))
    title = st.text_input("일정 제목")
    memo = st.text_area("메모")
    location = st.text_input("장소 또는 주소")
    edit_idx = st.selectbox("수정할 일정 선택 (선택 안 하면 새로 추가)", options=["새 일정"] + list(st.session_state.df.index))

    submitted = st.form_submit_button("저장")
    if submitted and is_admin:
        new_row = {
            "Date": date.strftime("%Y-%m-%d"),
            "Time": time.strftime("%H:%M"),
            "Title": title,
            "Memo": memo,
            "Location": location
        }
        if edit_idx == "새 일정":
            st.session_state.df.loc[len(st.session_state.df)] = new_row
        else:
            st.session_state.df.loc[edit_idx] = new_row
        st.session_state.df.to_csv(SCHEDULE_CSV, index=False)
        st.success("✅ 일정이 저장되었습니다.")
        st.experimental_rerun()

# 지도 표시
st.subheader("🗺️ 지도 보기")

# 지도 초기화
m = folium.Map(location=[DEFAULT_LAT, DEFAULT_LON], zoom_start=7)

# 지도에 마커 추가
geolocator = Nominatim(user_agent="calendar_app")
for _, row in st.session_state.df.iterrows():
    loc = row["Location"]
    try:
        location_obj = geolocator.geocode(loc)
        if location_obj:
            folium.Marker(
                location=[location_obj.latitude, location_obj.longitude],
                popup=f"{row['Title']}<br>{row['Date']} {row['Time']}<br>{loc}",
                icon=folium.Icon(color='red')
            ).add_to(m)
    except:
        continue

# 지도 출력
st_folium(m, width=700)

# 일정 리스트
st.subheader("📋 일정 목록")
for idx, row in st.session_state.df.iterrows():
    st.markdown(f"**{row['Date']} {row['Time']} ~** {row['Title']}")
    st.text(row["Memo"])
    st.markdown(f"📍 {row['Location']}")
    if is_admin:
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✏️ 수정", key=f"edit_{idx}"):
                st.experimental_set_query_params(edit=idx)
        with col2:
            if st.button("🗑️ 삭제", key=f"delete_{idx}"):
                st.session_state.df.drop(index=idx, inplace=True)
                st.session_state.df.to_csv(SCHEDULE_CSV, index=False)
                st.success("✅ 삭제 완료")
                st.experimental_rerun()

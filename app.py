import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_calendar import calendar
from geopy.geocoders import Nominatim
from datetime import datetime

# --------------------------------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="볼빨간사춘기 온오프라인 스케줄",
    page_icon="🎤",
    layout="wide",
)

st.title("🎤 볼빨간사춘기 온오프라인 스케줄")
st.caption(f"데이터 최종 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --------------------------------------------------------------------------
# CSV 데이터 로드 및 전처리
# --------------------------------------------------------------------------
# @st.cache_data를 사용해 앱 재실행 시 불필요한 파일 재로딩을 방지합니다.
@st.cache_data
def load_data():
    """schedule.csv 파일에서 스케줄 데이터를 불러와 DataFrame으로 변환합니다."""
    try:
        # GitHub 저장소에 함께 있는 schedule.csv 파일을 읽어옵니다.
        df = pd.read_csv("schedule.csv")

        # 데이터 전처리
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        # '도로명주소'가 비어있으면 '온라인', 아니면 '오프라인'으로 '구분' 열 추가
        df['구분'] = df['도로명주소'].apply(lambda x: '온라인' if pd.isna(x) or x == '' else '오프라인')
        return df
    except FileNotFoundError:
        st.error("`schedule.csv` 파일을 찾을 수 없습니다. `app.py`와 같은 위치에 파일이 있는지 확인해주세요.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로딩 중 오류 발생: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("스케줄 데이터가 비어있습니다. `schedule.csv` 파일을 확인해주세요.")
    st.stop()


# --------------------------------------------------------------------------
# 1. 캘린더 뷰 (전체 일정)
# --------------------------------------------------------------------------
st.header("🗓️ 전체 스케줄 (캘린더)")

# streamlit-calendar에 맞는 형식으로 데이터 가공
calendar_events = []
for index, row in df.iterrows():
    event = {
        "title": f"[{row['구분']}] {row['내용']}",
        "start": row['날짜'].strftime("%Y-%m-%d"),
        "color": "#FF4B4B" if row['구분'] == '오프라인' else "#00BFFF", # 오프라인은 빨간색, 온라인은 파란색
    }
    calendar_events.append(event)

calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay",
    },
    "initialView": "dayGridMonth",
    "events": calendar_events,
    "editable": False,
}

# 캘린더 렌더링 및 선택된 날짜 정보 받기
selected_date = calendar(
    events=calendar_events,
    options=calendar_options,
    custom_css="""
    .fc-event-past { opacity: 0.8; }
    .fc-event-time { font-style: italic; }
    .fc-event-title { font-weight: 700; }
    .fc-toolbar-title { font-size: 1.5rem; }
    """
)

# 캘린더에서 날짜를 클릭하면 해당 날짜의 상세 일정 표시
if selected_date.get('callback') == 'dateClick':
    clicked_date_str = selected_date.get('dateClick').get('dateStr')
    clicked_date = pd.to_datetime(clicked_date_str).date()
    
    st.subheader(f"📅 {clicked_date.strftime('%Y년 %m월 %d일')} 상세 일정")
    
    day_schedule = df[df['날짜'] == clicked_date]

    if not day_schedule.empty:
        for _, row in day_schedule.iterrows():
            badge_color = "red" if row['구분'] == "오프라인" else "blue"
            st.markdown(f"##### <span style='color:{badge_color};'>●</span> **{row['내용']}**", unsafe_allow_html=True)
            
            details = f"""
            - **시간:** {row['시간'] if pd.notna(row['시간']) else '미정'}
            - **장소/플랫폼:** {row['위치']}
            - **메모:** {row['메모'] if pd.notna(row['메모']) else '없음'}
            """
            if row['구분'] == '오프라인':
                details += f"\n- **주소:** {row['도로명주소']}"

            st.markdown(details)
            st.divider()

    else:
        st.info("해당 날짜에는 등록된 스케줄이 없습니다.")

st.divider()


# --------------------------------------------------------------------------
# 2. 온라인 / 3. 오프라인 일정 탭으로 분리
# --------------------------------------------------------------------------
tab1, tab2 = st.tabs(["💻 온라인 일정", "🎪 오프라인 일정 및 지도"])

# 온라인 일정 탭
with tab1:
    st.subheader("💻 온라인 스케줄 목록")
    online_df = df[df['구분'] == '온라인'].sort_values(by='날짜').reset_index(drop=True)

    if not online_df.empty:
        for index, row in online_df.iterrows():
            with st.expander(f"**{row['날짜'].strftime('%Y-%m-%d')}** | {row['내용']}"):
                st.markdown(f"**- 방송/플랫폼:** {row['위치']}")
                st.markdown(f"**- 시간:** {row['시간'] if pd.notna(row['시간']) else '미정'}")
                st.markdown(f"**- 메모:** {row['메모'] if pd.notna(row['메모']) else '없음'}")
    else:
        st.info("현재 예정된 온라인 스케줄이 없습니다.")

# 오프라인 일정 탭
with tab2:
    st.subheader("🎪 오프라인 스케줄 목록 및 지도")
    offline_df = df[df['구분'] == '오프라인'].sort_values(by='날짜').reset_index(drop=True)

    if not offline_df.empty:
        # Geocoding (주소 -> 위도/경도 변환)
        # 캐싱을 사용하여 반복적인 API 호출 방지
        @st.cache_data
        def geocode_address(address):
            """주소를 위도, 경도로 변환합니다."""
            geolocator = Nominatim(user_agent="bol4-schedule-app-csv")
            try:
                location = geolocator.geocode(address)
                if location:
                    return location.latitude, location.longitude
            except Exception:
                return None, None
            return None, None
        
        # 지도 생성 (대한민국 중심)
        m = folium.Map(location=[36.5, 127.5], zoom_start=7)

        # 오프라인 일정 목록 표시 및 지도에 핀 추가
        for index, row in offline_df.iterrows():
            address = row['도로명주소']
            lat, lon = geocode_address(address)

            # 상세 정보 카드
            with st.container(border=True):
                 st.markdown(f"**{row['날짜'].strftime('%Y-%m-%d')} | {row['내용']}**")
                 st.markdown(f"- **장소:** {row['위치']} ({row['도로명주소']})")
                 st.markdown(f"- **시간:** {row['시간'] if pd.notna(row['시간']) else '미정'}")
            
            # 지도에 마커 추가
            if lat and lon:
                popup_html = f"""
                <b>{row['내용']}</b><br>
                <b>장소:</b> {row['위치']}<br>
                <b>일시:</b> {row['날짜']} {row['시간']}
                """
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['내용']
                ).add_to(m)
            else:
                 st.warning(f"'{address}' 주소의 좌표를 찾을 수 없어 지도에 표시할 수 없습니다.")
            st.write("") # 간격 추가

        # Folium 지도 렌더링
        st.subheader("📍 스케줄 지도")
        st_folium(m, width=725, height=500)

    else:
        st.info("현재 예정된 오프라인 스케줄이 없습니다.")

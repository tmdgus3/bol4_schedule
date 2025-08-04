import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_calendar import calendar
from geopy.geocoders import Nominatim
from datetime import datetime
import pytz # 시간대 처리를 위해 pytz 라이브러리 import

# --------------------------------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="볼빨간사춘기 온오프라인 스케줄",
    page_icon="🎤",
    layout="wide",
)

st.title("🎤 볼빨간사춘기 온오프라인 스케줄")

# 정확한 한국 시간(KST)을 표시하도록 수정
KST = pytz.timezone('Asia/Seoul')
st.caption(f"데이터 최종 업데이트: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S %Z')}")

# --------------------------------------------------------------------------
# CSV 데이터 로드 및 전처리
# --------------------------------------------------------------------------
@st.cache_data
def load_data():
    """schedule.csv 파일에서 스케줄 데이터를 불러와 DataFrame으로 변환합니다."""
    try:
        df = pd.read_csv("schedule.csv")
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
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
st.header("🗓️ 전체 스케줄")

# 캘린더 이벤트 제목에서 [온라인/오프라인] 텍스트 제거
calendar_events = []
for index, row in df.iterrows():
    event = {
        "title": row['내용'], # <-- 내용만 표시하도록 수정
        "start": row['날짜'].strftime("%Y-%m-%d"),
        "color": "#FF4B4B" if row['구분'] == '오프라인' else "#00BFFF",
    }
    calendar_events.append(event)

# 캘린더 툴바에서 week, day 버튼 제거
calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth", # <-- 월(Month) 보기만 남김
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
            st.markdown(f"##### <span style='color:{badge_color};'>●</span> **{row['내용']}** ({row['구분']})", unsafe_allow_html=True)
            
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

with tab1:
    st.subheader("💻 온라인 스케줄 목록")
    # ... (내용 동일) ...
    online_df = df[df['구분'] == '온라인'].sort_values(by='날짜', ascending=False).reset_index(drop=True)

    if not online_df.empty:
        for index, row in online_df.iterrows():
            with st.expander(f"**{row['날짜'].strftime('%Y-%m-%d')}** | {row['내용']}"):
                st.markdown(f"**- 방송/플랫폼:** {row['위치']}")
                st.markdown(f"**- 시간:** {row['시간'] if pd.notna(row['시간']) else '미정'}")
                st.markdown(f"**- 메모:** {row['메모'] if pd.notna(row['메모']) else '없음'}")
    else:
        st.info("현재 예정된 온라인 스케줄이 없습니다.")


with tab2:
    st.subheader("🎪 오프라인 스케줄 목록 및 지도")
    # ... (내용 동일, 지도 부분만 수정) ...
    offline_df = df[df['구분'] == '오프라인'].sort_values(by='날짜', ascending=False).reset_index(drop=True)

    if not offline_df.empty:
        @st.cache_data
        def geocode_address(address):
            geolocator = Nominatim(user_agent="bol4-schedule-app-csv")
            try:
                location = geolocator.geocode(address)
                if location:
                    return location.latitude, location.longitude
            except Exception:
                return None, None
            return None, None
        
        m = folium.Map(location=[36.5, 127.5], zoom_start=7)

        for index, row in offline_df.iterrows():
            with st.container(border=True):
                 st.markdown(f"**{row['날짜'].strftime('%Y-%m-%d')} | {row['내용']}**")
                 st.markdown(f"- **장소:** {row['위치']} ({row['도로명주소']})")
                 st.markdown(f"- **시간:** {row['시간'] if pd.notna(row['시간']) else '미정'}")
            
            address = row['도로명주소']
            lat, lon = geocode_address(address)
            if lat and lon:
                popup_html = f"<b>{row['내용']}</b><br><b>장소:</b> {row['위치']}"
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['내용']
                ).add_to(m)
            else:
                 st.warning(f"'{address}' 주소의 좌표를 찾을 수 없어 지도에 표시할 수 없습니다.", icon="📍")
            st.write("") 

        st.subheader("📍 스케줄 지도")
        # 모바일 최적화를 위해 use_container_width=True 사용
        st_folium(m, use_container_width=True, height=500)

    else:
        st.info("현재 예정된 오프라인 스케줄이 없습니다.")

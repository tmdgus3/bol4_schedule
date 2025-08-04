import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_calendar import calendar
from geopy.geocoders import Nominatim
from datetime import datetime
import pytz
import os

# --------------------------------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="볼빨간사춘기 온오프라인 스케줄",
    page_icon="🎤",
    layout="wide",
)

st.title("🎤 볼빨간사춘기 온오프라인 스케줄")

# 'schedule.csv' 파일의 최종 수정 시간을 기준으로 업데이트 시간 표시
KST = pytz.timezone('Asia/Seoul')
try:
    mod_time_unix = os.path.getmtime("schedule.csv")
    mod_time_kst = datetime.fromtimestamp(mod_time_unix, KST)
    st.caption(f"데이터 최종 업데이트: {mod_time_kst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
except FileNotFoundError:
    st.caption("schedule.csv 파일을 찾을 수 없습니다.")


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

# 오늘 날짜 정의
today_date = datetime.now(KST).date()

# 캘린더 이벤트 색상 로직 변경
calendar_events = []
for index, row in df.iterrows():
    event_date = row['날짜']
    
    # 날짜에 따른 색상 결정
    if event_date < today_date:
        color = "grey"
    else:
        color = "#FF4B4B" if row['구분'] == '오프라인' else "#00BFFF"
    
    event = {
        "title": row['내용'],
        "start": event_date.strftime("%Y-%m-%d"),
        "color": color,
    }
    calendar_events.append(event)

# 캘린더 옵션: 높이 자동 조절, 툴바 단순화
calendar_options = {
    "height": "auto",
    "headerToolbar": {
        "left": "prev,next",
        "center": "title",
        "right": "",
    },
    "initialView": "dayGridMonth",
    "events": calendar_events,
    "editable": False,
}

selected_date = calendar(events=calendar_events, options=calendar_options)

# 캘린더 색상 범례(Index) 추가
st.markdown(
    """
    <div style="text-align: right; font-size: 0.8em; margin-top: 5px;">
        <span style="background-color: grey; padding: 2px 6px; margin: 0 4px 0 8px; border-radius: 4px;">&nbsp;</span> 지난 일정 &nbsp;
        <span style="background-color: #00BFFF; padding: 2px 6px; margin: 0 4px 0 8px; border-radius: 4px;">&nbsp;</span> 온라인 &nbsp;
        <span style="background-color: #FF4B4B; padding: 2px 6px; margin: 0 4px 0 8px; border-radius: 4px;">&nbsp;</span> 오프라인
    </div>
    """,
    unsafe_allow_html=True
)


# 캘린더에서 날짜를 클릭하면 해당 날짜의 상세 일정 표시
if selected_date.get('callback') == 'dateClick':
    clicked_date_str = selected_date.get('dateClick').get('dateStr')
    clicked_date = pd.to_datetime(clicked_date_str).date()
    
    st.subheader(f"📅 {clicked_date.strftime('%Y년 %m월 %d일')} 상세 일정")
    day_schedule = df[df['날짜'] == clicked_date]

    if not day_schedule.empty:
        for _, row in day_schedule.iterrows():
            is_past = row['날짜'] < today_date
            style = "color: grey;" if is_past else ""
            badge_color = "grey" if is_past else ("red" if row['구분'] == "오프라인" else "blue")

            st.markdown(f"<h5 style='{style}'><span style='color:{badge_color};'>●</span> <b>{row['내용']}</b> ({row['구분']})</h5>", unsafe_allow_html=True)
            st.markdown(f"<div style='{style}'>- <b>시간:</b> {row['시간'] if pd.notna(row['시간']) else '미정'}<br>- <b>장소/플랫폼:</b> {row['위치']}<br>- <b>메모:</b> {row['메모'] if pd.notna(row['메모']) else '없음'}</div>", unsafe_allow_html=True)
            
            if row['구분'] == '오프라인' and pd.notna(row['도로명주소']):
                st.markdown(f"<div style='{style}'>- <b>주소:</b> {row['도로명주소']}</div>", unsafe_allow_html=True)
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
    online_df = df[df['구분'] == '온라인'].sort_values(by='날짜', ascending=True).reset_index(drop=True)

    if not online_df.empty:
        for index, row in online_df.iterrows():
            is_past = row['날짜'] < today_date
            style_tag = "style='color:grey;'" if is_past else ""
            
            with st.expander(f"**{row['날짜'].strftime('%Y-%m-%d')}** | {row['내용']}"):
                # 수정된 부분: 상세 정보가 올바르게 표시되도록 복원
                st.markdown(
                    f"<div {style_tag}>"
                    f"<b>- 방송/플랫폼:</b> {row['위치']}<br>"
                    f"<b>- 시간:</b> {row['시간'] if pd.notna(row['시간']) else '미정'}<br>"
                    f"<b>- 메모:</b> {row['메모'] if pd.notna(row['메모']) else '없음'}"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        st.info("현재 예정된 온라인 스케줄이 없습니다.")

with tab2:
    st.subheader("🎪 오프라인 스케줄 목록 및 지도")
    offline_df = df[df['구분'] == '오프라인'].sort_values(by='날짜', ascending=True).reset_index(drop=True)

    if not offline_df.empty:
        @st.cache_data
        def geocode_address(address):
            geolocator = Nominatim(user_agent="bol4-schedule-app-final")
            try: return geolocator.geocode(address)
            except Exception: return None

        m = folium.Map(location=[36.5, 127.5], zoom_start=7)

        for index, row in offline_df.iterrows():
            is_past = row['날짜'] < today_date
            style_tag = "style='color:grey;'" if is_past else ""

            with st.container(border=True):
                 # 수정된 부분: 상세 정보가 올바르게 표시되도록 복원
                st.markdown(
                    f"<div {style_tag}>"
                    f"<b>{row['날짜'].strftime('%Y-%m-%d')} | {row['내용']}</b><br>"
                    f"- <b>장소:</b> {row['위치']} ({row['도로명주소']})<br>"
                    f"- <b>시간:</b> {row['시간'] if pd.notna(row['시간']) else '미정'}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            if pd.notna(row['도로명주소']):
                location = geocode_address(row['도로명주소'])
                if location:
                    popup_html = f"<b>{row['내용']}</b><br><b>장소:</b> {row['위치']}"
                    marker_icon = 'ok-sign' if not is_past else 'time'
                    marker_color = 'red' if not is_past else 'gray'
                    folium.Marker(
                        [location.latitude, location.longitude],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=row['내용'],
                        icon=folium.Icon(color=marker_color, icon=marker_icon, prefix='glyphicon')
                    ).add_to(m)

        st.subheader("📍 스케줄 지도")
        st_folium(m, use_container_width=True, height=500)
    else:
        st.info("현재 예정된 오프라인 스케줄이 없습니다.")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import datetime
import pytz
import calendar
import matplotlib.pyplot as plt

# 📁 CSV 파일 경로
DATA_PATH = "schedule.csv"

# 📍 마커 색상 정의
pin_colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "darkgreen"]

# 📄 CSV 불러오기
@st.cache_data
def load_data():
    if not DATA_PATH:
        return pd.DataFrame(columns=["날짜", "시간", "내용", "메모", "위치", "도로명주소"])
    df = pd.read_csv(DATA_PATH)
    df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
    return df

df = load_data()

# 📆 오늘 날짜
today = datetime.date.today()

# 🎨 일정 있는 날짜 색상 매핑
def get_date_color_map(df):
    date_color_map = {}
    for i, row in df.iterrows():
        date = row["날짜"]
        if pd.isna(row["도로명주소"]) or row["도로명주소"].strip() == "":
            date_color_map[date] = "red"  # 온라인 일정
        else:
            date_color_map[date] = pin_colors[i % len(pin_colors)]  # 오프라인
    return date_color_map

# 📅 달력 그리기 함수
def draw_colored_calendar(year, month, date_color_map, selected_date=None):
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_axis_off()

    for i, day_name in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
        ax.text(i, len(month_days), day_name, ha='center', va='center', fontsize=12, weight='bold')

    for week_idx, week in enumerate(month_days):
        for day_idx, day in enumerate(week):
            if day != 0:
                date_obj = datetime.date(year, month, day)
                color = date_color_map.get(date_obj, "black")
                weight = "bold" if selected_date == date_obj else "normal"
                ax.text(day_idx, len(month_days) - week_idx - 1, str(day),
                        ha='center', va='center', fontsize=12, color=color, weight=weight)

    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(-0.5, len(month_days) + 0.5)
    plt.title(f"{year}년 {month}월", fontsize=16)
    plt.tight_layout()
    return fig

# ✅ Streamlit 시작
st.set_page_config(page_title="볼빨간사춘기 스케줄 관리", layout="wide")
st.title("📅 볼빨간사춘기 스케줄 관리")

# 🕒 최종 수정일 표시
if DATA_PATH:
    kst = pytz.timezone("Asia/Seoul")
    modified_time = datetime.datetime.fromtimestamp(
        os.path.getmtime(DATA_PATH), tz=kst
    )
    st.caption(f"📌 최종 수정일: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 📅 달력
st.subheader("🗓️ 일정 달력")
date_color_map = get_date_color_map(df)
fig_aug = draw_colored_calendar(2025, 8, date_color_map)
fig_sep = draw_colored_calendar(2025, 9, date_color_map)
st.pyplot(fig_aug)
st.pyplot(fig_sep)

# 📆 날짜 선택
selected_date = st.date_input("날짜를 선택하세요", value=today)

# 🗂 일정 필터링
selected_str = selected_date.strftime("%Y-%m-%d")
online_df = df[df["도로명주소"].isna() | (df["도로명주소"].str.strip() == "")]
offline_df = df[~df.index.isin(online_df.index)]
selected_online = online_df[online_df["날짜"] == selected_date]
selected_offline = offline_df[offline_df["날짜"] == selected_date]

# 🏟️ 오프라인 일정
st.subheader("🏟️ 오프라인 일정")
if not selected_offline.empty:
    for i, row in selected_offline.iterrows():
        color = pin_colors[i % len(pin_colors)]
        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")
        st.markdown(f"⬤ <span style='color:{color}'>{row['위치']}</span>", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['도로명주소']}", unsafe_allow_html=True)
        if pd.notna(row["메모"]) and row["메모"].strip():
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}", unsafe_allow_html=True)
else:
    st.info("해당 날짜에 오프라인 일정이 없습니다.")

# 💻 온라인 일정
st.subheader("💻 온라인 일정")
if not selected_online.empty:
    for i, row in selected_online.iterrows():
        st.markdown(f"**{row['날짜']} {row['시간']} - {row['내용']}**")
        st.markdown(f"⬤ {row['위치']}")
        if pd.notna(row["메모"]) and row["메모"].strip():
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{row['메모']}")
else:
    st.info("해당 날짜에 온라인 일정이 없습니다.")

# 🗺️ 지도
st.subheader("🗺️ 오프라인 위치 보기")
geolocator = Nominatim(user_agent="bol4_schedule_app")
m = folium.Map(location=[36.5, 127.8], zoom_start=7)
m.fit_bounds([[33.0, 124.5], [38.7, 131.2]])  # 대한민국 본토 제한

for i, row in offline_df.iterrows():
    color = pin_colors[i % len(pin_colors)]
    if pd.notna(row["도로명주소"]):
        try:
            location = geolocator.geocode(row["도로명주소"])
            if location:
                folium.Marker(
                    location=[location.latitude, location.longitude],
                    popup=row["내용"],
                    icon=folium.Icon(color=color, icon="info-sign")
                ).add_to(m)
        except:
            continue

st_folium(m, width=800, height=450)

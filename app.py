import streamlit as st
import pandas as pd
import os
import datetime

DATA_PATH = "schedule.csv"

# 일정 데이터 불러오기
def load_schedule():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["Date", "Time", "Title", "Memo"])

# 일정 저장
def save_schedule(df):
    df.to_csv(DATA_PATH, index=False)

st.title("📅 일정 관리 앱")
st.write("※ 아래에 비밀번호를 입력하면 일정을 추가할 수 있어요.")

# 비밀번호 입력
password = st.sidebar.text_input("🔒 비밀번호", type="password")
can_edit = password == "bol4pass"  # ← 여기 비밀번호 원하는 걸로 바꿔도 돼요

df = load_schedule()

# 일정 추가 (비밀번호 맞은 경우만)
if can_edit:
    st.subheader("📌 새 일정 추가")
    with st.form("new_schedule_form"):
        date = st.date_input("날짜", datetime.date.today())
        time = st.time_input("시간", datetime.datetime.now().time())
        title = st.text_input("제목")
        memo = st.text_area("메모")
        submitted = st.form_submit_button("저장")

        if submitted:
            new_row = pd.DataFrame([[date, time, title, memo]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_schedule(df)
            st.success("✅ 저장 완료!")

# 일정 전체 보기
st.subheader("📖 전체 일정")
st.dataframe(df.sort_values(by=["Date", "Time"]))

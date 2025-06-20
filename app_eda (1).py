import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                    EDA를 통해 파일을 분석하려면 로그인을 해 주세요
                    이후 EDA 탭에서 분석할 수 있습니다.
                    """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 인구 통계 분석 (population_trends.csv)")
        uploaded = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        df.replace('-', 0, inplace=True)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화"
        ])

        with tabs[0]:
            st.header("🔍 데이터 구조 및 기초 통계")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
            st.dataframe(df.describe())
            st.dataframe(df.isnull().sum())
            st.write(f"중복 행 개수: {df.duplicated().sum()}개")

        with tabs[1]:
            st.header("📈 연도별 전체 인구 추이 (전국)")
            df_national = df[df['지역'] == '전국']
            yearly = df_national.groupby('연도').agg({
                '인구': 'sum',
                '출생아수(명)': 'sum',
                '사망자수(명)': 'sum'
            }).reset_index()

            recent = yearly.tail(3)
            net_growth = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_year = yearly['연도'].max()
            last_pop = yearly[yearly['연도'] == last_year]['인구'].values[0]
            predicted_2035 = last_pop + (2035 - last_year) * net_growth

            fig, ax = plt.subplots()
            sns.lineplot(data=yearly, x='연도', y='인구', marker='o', ax=ax)
            ax.axvline(2035, color='gray', linestyle='--')
            ax.scatter([2035], [predicted_2035], color='red')
            ax.text(2035, predicted_2035, f"2035: {int(predicted_2035):,}", color='red', va='bottom')
            ax.set_title("Population Trend")
            ax.set_ylabel("Population")
            ax.set_xlabel("Year")
            st.pyplot(fig)

        with tabs[2]:
            st.header("🌍 지역별 최근 5년 인구 변화")
            latest_year = df['연도'].max()
            base_year = latest_year - 5
            df_filtered = df[df['지역'] != '전국']
            df_latest = df_filtered[df_filtered['연도'] == latest_year].set_index('지역')
            df_base = df_filtered[df_filtered['연도'] == base_year].set_index('지역')
            delta = df_latest['인구'] - df_base['인구']
            delta_sorted = delta.sort_values(ascending=False) / 1000

            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=delta_sorted.values, y=delta_sorted.index, ax=ax1, palette="Blues_r")
            for i, v in enumerate(delta_sorted.values):
                ax1.text(v + 5, i, f"{v:.0f}", va='center')
            ax1.set_title("Population Change (5 yrs)")
            ax1.set_xlabel("Population Change (thousands)")
            ax1.set_ylabel("")
            st.pyplot(fig1)

            ratio = ((df_latest['인구'] - df_base['인구']) / df_base['인구']) * 100
            ratio_sorted = ratio.sort_values(ascending=False)
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=ratio_sorted.values, y=ratio_sorted.index, ax=ax2, palette="Reds_r")
            for i, v in enumerate(ratio_sorted.values):
                ax2.text(v + 0.5, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Growth Rate (5 yrs)")
            ax2.set_xlabel("Growth Rate (%)")
            ax2.set_ylabel("")
            st.pyplot(fig2)

            st.markdown("""
                **Interpretation:**
                - The top region shows the highest absolute growth in population over the past 5 years.
                - Growth rate comparison highlights fast-growing regions regardless of their size.
                - This insight is useful for resource allocation and regional policy planning.
            """)

        with tabs[3]:
            st.header("📊 증감률 상위 지역 및 연도")
            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['이전인구'] = df_sorted.groupby('지역')['인구'].shift(1)
            df_sorted['증감'] = df_sorted['인구'] - df_sorted['이전인구']
            df_sorted['증감률(%)'] = ((df_sorted['증감']) / df_sorted['이전인구']) * 100
            top_diff = df_sorted[df_sorted['지역'] != '전국'].sort_values('증감', ascending=False).head(100)

            styled_table = top_diff[['연도', '지역', '이전인구', '인구', '증감']].copy()
            styled_table['이전인구'] = styled_table['이전인구'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else '')
            styled_table['인구'] = styled_table['인구'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else '')
            styled_table['증감'] = styled_table['증감'].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else '')

            def highlight_diff(val):
                try:
                    val_int = int(val.replace(',', ''))
                    color = 'background-color: #d0f0fd' if val_int > 0 else 'background-color: #fddddd'
                    return color
                except:
                    return ''

            st.dataframe(
                styled_table.style.applymap(highlight_diff, subset=['증감'])
            )

        with tabs[4]:
            st.header("📊 누적 영역 그래프")
            df_area = df[df['지역'] != '전국']
            pivot = df_area.pivot_table(index='연도', columns='지역', values='인구', aggfunc='sum')
            pivot.columns.name = None
            pivot = pivot.sort_index()

            fig, ax = plt.subplots(figsize=(14, 7))
            x = pivot.index
            y = pivot.values.T  # shape: (지역 수, 연도 수)
            colors = plt.cm.tab20(np.linspace(0, 1, len(pivot.columns)))
            ax.stackplot(x, y, labels=pivot.columns, colors=colors)
            ax.set_title("Stacked Area: Population by Region")
            ax.set_ylabel("Population")
            ax.set_xlabel("Year")
            ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
            st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
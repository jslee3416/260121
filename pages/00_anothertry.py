import streamlit as st
import pandas as pd
import os
import urllib.parse

st.set_page_config(page_title="서울 맛집 검색", layout="wide")

# 1. 경로 자동 탐색 함수
def get_csv_path():
    # os.path.expanduser("~")는 C:\Users\사용자명 까지를 자동으로 찾아줍니다.
    base_path = os.path.join(os.path.expanduser("~"), "Downloads")
    file_name = "restaurantinseoul.csv"
    return os.path.join(base_path, file_name)

CSV_PATH = get_csv_path()

@st.cache_data
def load_and_process_data(path):
    # [디버그] 파일이 진짜 있는지 다시 확인
    if not os.path.exists(path):
        return "NOT_FOUND"

    try:
        container = []
        # 한글 깨짐 방지 인코딩 자동 시도
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # 메모리 절약을 위해 3개 컬럼만, 5만 줄씩 끊어서 읽기
                reader = pd.read_csv(path, usecols=[3, 8, 9], chunksize=50000, encoding=enc)
                for chunk in reader:
                    chunk.columns = ['status', 'name', 'category']
                    # '폐업' 제외 및 '영업/정상' 데이터 유지
                    filtered = chunk[chunk['status'].fillna('').str.contains("영업|정상")].copy()
                    filtered = filtered[~filtered['status'].fillna('').str.contains("폐업")].copy()
                    container.append(filtered)
                
                return pd.concat(container, ignore_index=True)
            except UnicodeDecodeError:
                continue
        return "ENCODING_ERROR"
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- 메인 화면 ---
st.title("🍴 서울시 맛집 정보 서비스")

# 현재 프로그램이 인식하고 있는 경로 표시 (문제가 있다면 이 경로를 확인하세요)
st.sidebar.write("### 📂 시스템 경로 확인")
st.sidebar.code(CSV_PATH)

if not os.path.exists(CSV_PATH):
    st.error(f"❌ 파일을 찾을 수 없습니다.")
    st.markdown(f"""
    **현재 프로그램이 찾고 있는 위치:** `{CSV_PATH}`
    
    **조치 방법:**
    1. 다운로드 폴더에 파일 이름이 정확히 `restaurantinseoul.csv` 인지 확인하세요.
    2. 파일 확장자가 숨겨져서 `restaurantinseoul.csv.csv`는 아닌지 확인하세요.
    """)
else:
    with st.spinner('149MB 데이터를 고속 처리 중입니다...'):
        df = load_and_process_data(CSV_PATH)

    if isinstance(df, str):
        st.error(f"❌ 로딩 오류: {df}")
    else:
        st.success(f"✅ {len(df):,}개의 영업 중인 식당 데이터를 불러왔습니다.")

        # 2. LoV (10번째 컬럼이었던 'category')
        categories = sorted(df['category'].dropna().unique().tolist())
        selected = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

        # 3. 필터링 및 결과 (Top 20)
        view_df = df if selected == "전체" else df[df['category'] == selected]
        
        st.subheader(f"📍 '{selected}' 검색 결과 (Top 20)")
        
        for i, row in view_df.head(20).iterrows():
            # 구글 검색 링크 생성
            query = urllib.parse.quote(f"서울 {row['name']} {row['category']}")
            url = f"https://www.google.com/search?q={query}"
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{row['name']}** ({row['category']})")
                col2.markdown(f"[⭐ 구글검색]({url})")
                st.divider()

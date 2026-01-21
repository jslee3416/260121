import streamlit as st
import pandas as pd
import urllib.parse
import os

st.set_page_config(page_title="서울 맛집 파인더", layout="wide")

# --- 진단 모드: 파일이 실제로 있는지 확인 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
files_in_dir = os.listdir(current_dir)

st.sidebar.write("### 📂 서버 파일 시스템 확인")
st.sidebar.write(f"현재 위치: `{current_dir}`")
st.sidebar.write("찾은 파일들:", files_in_dir)

DATA_FILE = "restaurants.csv"

# 파일이 목록에 없는 경우 경고 출력
if DATA_FILE not in files_in_dir:
    st.error(f"❌ '{DATA_FILE}' 파일이 저장소에 없습니다!")
    st.info(f"현재 인식된 파일 중 가장 유사한 이름: {[f for f in files_in_dir if 'csv' in f]}")
# --- 진단 모드 끝 ---

@st.cache_data
def load_and_clean_data(file_name):
    try:
        # 파일 경로 설정
        file_path = os.path.join(current_dir, file_name)
        
        # 인코딩 순차 시도
        df = None
        for enc in ['utf-8', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                if df is not None and not df.empty:
                    break
            except:
                continue
        
        if df is None or df.empty:
            return pd.DataFrame()

        # 컬럼 매칭
        name_map = {'식당명': '상호', '지역명': '지역', '대표메뉴명': '대표메뉴'}
        existing_cols = [c for c in name_map.keys() if c in df.columns]
        df = df[existing_cols].rename(columns=name_map)
        
        # 구/동 분리
        def split_region(x):
            if pd.isna(x): return "미분류", "미분류"
            parts = str(x).split()
            gu = parts[0] if len(parts) > 0 else "미분류"
            dong = parts[1] if len(parts) > 1 else "전체"
            return gu, dong

        df[['구', '동']] = df['지역'].apply(lambda x: pd.Series(split_region(x)))
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 로드 오류 발생: {e}")
        return pd.DataFrame()

df = load_and_clean_data(DATA_FILE)

# (이하 UI 로직은 이전과 동일...)
if not df.empty:
    st.success(f"✅ {DATA_FILE} 데이터를 성공적으로 불러왔습니다!")
    # ... (기존 UI 코드)
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    dong_options = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", ["전체"] + dong_options)
    
    filtered_df = df[(df['구'] == selected_gu)]
    if selected_dong != "전체":
        filtered_df = filtered_df[filtered_df['동'] == selected_dong]
        
    st.title(f"🍴 {selected_gu} {selected_dong} 맛집 리스트")
    st.dataframe(filtered_df[['상호', '대표메뉴', '구', '동']], use_container_width=True)

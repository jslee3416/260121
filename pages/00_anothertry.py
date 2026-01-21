import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

st.set_page_config(page_title="서울 맛집 데이터 진단", layout="wide")

GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_and_diagnose(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 1. 인코딩 시도 및 전체 데이터 읽기 (상위 100줄만 우선 분석)
        df = pd.read_csv(io.BytesIO(response.content), encoding='cp949', low_memory=False)
        
        # 2. [진단용] 모든 컬럼명과 인덱스 번호를 정리
        col_info = [{"인덱스": i, "컬럼명": col, "샘플데이터": str(df[col].iloc[0])} for i, col in enumerate(df.columns)]
        
        return df, col_info
    except Exception as e:
        return None, str(e)

# --- 메인 화면 ---
st.title("🍴 서울시 맛집 데이터 진단 도구")

with st.spinner('데이터 구조를 분석 중입니다...'):
    df, info = load_and_diagnose(DIRECT_URL)

if df is None:
    st.error(f"데이터 로드 실패: {info}")
else:
    # --- 1단계: 데이터 구조 보여주기 (개발자 도구 역할) ---
    with st.expander("🔍 데이터 실제 구조 확인하기 (여기를 클릭해서 컬럼 번호를 확인하세요)"):
        st.write("이 표를 보고 '영업상태', '사업장명', '업태명'이 몇 번 인덱스인지 확인해 주세요.")
        st.table(info)
    
    # --- 2단계: 안전한 컬럼 추출 ---
    # 사용자가 말한 4, 9, 10번째(인덱스 3, 8, 9)를 시도하되, 
    # 데이터가 0개면 필터링을 풀고 원본을 보여줍니다.
    try:
        working_df = df.iloc[:, [3, 8, 9]].copy()
        working_df.columns = ['status', 'name', 'category']
        
        # 필터링 전 원본 데이터 건수
        total_count = len(working_df)
        
        # '폐업'이 포함되지 않은 것만 필터링 (필터링 조건을 아주 약하게 설정)
        active_df = working_df[~working_df['status'].fillna('').str.contains("폐업|취소", na=False)].copy()
        
        st.success(f"✅ 전체 {total_count:,}개 중 '폐업' 제외 {len(active_df):,}개를 찾았습니다.")
        
        # --- 3단계: 카테고리 선택 및 결과 ---
        categories = sorted(active_df['category'].dropna().unique().tolist())
        
        if not categories:
            st.warning("⚠️ 카테고리(업종) 데이터를 찾을 수 없습니다. 컬럼 번호가 맞는지 위 표에서 확인하세요.")
        else:
            selected = st.selectbox("🎯 업종을 선택하세요", ["전체"] + categories)
            
            final_df = active_df if selected == "전체" else active_df[active_df['category'] == selected]
            
            st.subheader(f"📍 '{selected}' 결과 (상위 20개)")
            for i, row in final_df.head(20).iterrows():
                query = urllib.parse.quote(f"서울 {row['name']} {row['category']}")
                url = f"https://www.google.com/search?q={query}"
                
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{row['name']}**")
                col1.caption(f"상태: {row['status']} | 업종: {row['category']}")
                col2.markdown(f"[⭐ 구글검색]({url})")
                st.divider()
                
    except Exception as e:
        st.error(f"컬럼 추출 중 오류 발생: {e}. 데이터의 컬럼 수가 부족할 수 있습니다.")

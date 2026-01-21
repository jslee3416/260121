import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 평점 파인더", layout="wide")

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()

        # 인코딩 시도 (CP949 -> UTF-8 순서)
        df = None
        for enc in ['cp949', 'utf-8-sig', 'utf-8', 'euc-kr']:
            try:
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                if df is not None and not df.empty:
                    df.columns = df.columns.str.strip() # 컬럼명 공백 제거
                    break
            except:
                continue
        
        if df is None: return pd.DataFrame()

        # [핵심] 식당명과 지역명 컬럼만 추출
        # 파일 내 실제 컬럼명이 '식당명', '지역명' 인지 확인하고 가져옵니다.
        target_cols = {
            '식당명': next((c for c in df.columns if '식당명' in c), None),
            '지역명': next((c for c in df.columns if '지역명' in c), None)
        }

        if not target_cols['식당명'] or not target_cols['지역명']:
            st.error(f"파일에 '식당명' 또는 '지역명' 컬럼이 없습니다. (현재 컬럼: {df.columns.tolist()})")
            return pd.DataFrame()

        # 필요한 데이터만 복사
        new_df = df[[target_cols['식당명'], target_cols['지역명']]].copy()
        new_df.columns = ['상호', '지역']
        
        # [행정구역 추출] 지역명에서 첫 번째 단어(예: 강남구)만 가져와 '구' 컬럼 생성
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "미분류")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame()

# 데이터 실행
df = load_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.caption("서울관광재단 정보를 기반으로 구글 맵 실시간 평점을 연결합니다.")

if not df.empty:
    # 사이드바: 자치구 선택 (행정구역)
    st.sidebar.header("📍 지역 필터")
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구(구)를 선택하세요", ["전체"] + gu_list)
    
    # 데이터 필터링
    filtered_df = df
    if selected_gu != "전체":
        filtered_df = df[df['구'] == selected_gu]

    # 검색바
    search_q = st.sidebar.text_input("🔍 식당 이름 검색", "")
    if search_q:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_q, na=False)]

    # 결과 요약
    st.subheader(f"📍 {selected_gu} 지역 식당 목록")
    st.write(f"총 **{len(filtered_df)}**개의 식당이 검색되었습니다.")

    # 3. 결과 리스트 (표 형식)
    if not filtered_df.empty:
        # 페이지네이션
        rows_per_page = 20
        total_pages = max(len(filtered_df) // rows_per_page + 1, 1)
        current_page = st.number_input(f"페이지 (1/{total_pages})", 1, total_pages, 1)
        
        start_idx = (current_page - 1) * rows_per_page
        page_data = filtered_df.iloc[start_idx : start_idx + rows_per_page]

        st.markdown("---")
        # 테이블 헤더
        st.markdown("| 번호 | 식당명 | 상세 주소(지역) | 구글 맵 평점 연결 |")
        st.markdown("| :--- | :--- | :--- | :--- |")
        
        for i, (_, row) in enumerate(page_data.iterrows()):
            # 구글 검색 링크: "지역명 + 식당명" 조합으로 정확도 향상
            search_text = f"{row['지역']} {row['상호']}"
            google_url = f"https://www.google.com/maps/search/{urllib.parse.quote(search_text)}"
            
            st.markdown(f"| {start_idx + i + 1} | **{row['상호']}** | {row['지역']} | [⭐ 평점 확인하기]({google_url}) |")
    else:
        st.info("검색 결과가 없습니다.")
else:
    st.error("데이터 로드에 실패했습니다. GitHub의 restaurants.csv 파일과 컬럼명을 확인해 주세요.")

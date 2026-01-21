import streamlit as st
import pandas as pd
import urllib.parse
import os

st.set_page_config(page_title="서울 맛집 파인더", layout="wide")

# 1. 파일 경로 정의
# Streamlit Cloud 환경에서 가장 안전한 경로 지정 방식입니다.
DATA_FILE = "restaurants.csv"

@st.cache_data
def load_and_clean_data(file_name):
    try:
        # 현재 실행 중인 파일(main.py)과 같은 폴더에서 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 파일이 존재하는지 최종 확인
        if not os.path.exists(file_path):
            st.error(f"서버 내에 {file_name} 파일이 존재하지 않습니다.")
            return pd.DataFrame()

        # 인코딩 및 구분자 자동 감지 로직 강화
        df = None
        # 공공데이터는 cp949가 가장 많으므로 먼저 시도합니다.
        for enc in ['cp949', 'utf-8', 'euc-kr']:
            try:
                # sep=None, engine='python'은 쉼표/탭 등을 자동으로 찾아줍니다.
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                if df is not None and not df.empty and len(df.columns) > 1:
                    break
            except:
                continue
        
        if df is None or df.empty:
            st.error("파일을 읽었으나 데이터가 비어있거나 형식이 올바르지 않습니다.")
            return pd.DataFrame()

        # [컬럼 매칭] 실제 파일 내 컬럼명과 연결
        # 제공해주신 정보 기준: '식당명', '지역명', '대표메뉴명'
        name_map = {
            '식당명': '상호',
            '지역명': '지역',
            '대표메뉴명': '대표메뉴'
        }
        
        # 실제 파일에 있는 컬럼만 골라내기
        existing_cols = [c for c in name_map.keys() if c in df.columns]
        df = df[existing_cols].rename(columns=name_map).copy()
        
        # 행정구역(구/동) 분리 함수
        def split_region(x):
            if pd.isna(x): return "미분류", "미분류"
            parts = str(x).split()
            gu = parts[0] if len(parts) > 0 else "미분류"
            # 구 뒤에 오는 모든 글자를 동으로 합침
            dong = " ".join(parts[1:]) if len(parts) > 1 else "전체"
            return gu, dong

        # 지역 컬럼이 있을 때만 분리 실행
        if '지역' in df.columns:
            df[['구', '동']] = df['지역'].apply(lambda x: pd.Series(split_region(x)))
        else:
            # 지역 컬럼이 없으면 임시 데이터 생성
            df['구'] = "서울전체"
            df['동'] = "전체"
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 로드 중 시스템 오류: {e}")
        return pd.DataFrame()

# 데이터 로드 실행
df = load_and_clean_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.markdown("---")

if not df.empty:
    st.sidebar.success("✅ 데이터를 성공적으로 불러왔습니다!")
    
    # 사이드바 필터
    st.sidebar.header("📍 지역 필터")
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    dong_options = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", ["전체"] + dong_options)
    
    # 데이터 필터링
    filtered_df = df[df['구'] == selected_gu]
    if selected_dong != "전체":
        filtered_df = filtered_df[filtered_df['동'] == selected_dong]

    # 검색 기능
    search_query = st.sidebar.text_input("🔍 식당 이름 검색", "")
    if search_query:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_query, na=False)]

    st.subheader(f"📍 {selected_gu} {selected_dong if selected_dong != '전체' else ''} 맛집 목록")
    st.write(f"검색 결과: 총 **{len(filtered_df)}**개")

    # 3. 결과 출력 (표 형식 및 구글맵 링크)
    if not filtered_df.empty:
        rows_per_page = 15
        total_pages = max(len(filtered_df) // rows_per_page + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
        current_page = st.number_input(f"페이지 (1/{total_pages})", 1, total_pages, 1)
        
        start_idx = (current_page - 1) * rows_per_page
        page_data = filtered_df.iloc[start_idx : start_idx + rows_per_page].copy()

        def make_google_link(row):
            search_text = f"{row['구']} {row['동']} {row['상호']}"
            return f"https://www.google.com/maps/search/{urllib.parse.quote(search_text)}"

        st.markdown("---")
        # 테이블 헤더
        st.markdown("| 번호 | 식당명 | 대표메뉴 | 실시간 구글 평점 링크 |")
        st.markdown("| :--- | :--- | :--- | :--- |")
        
        for i, (_, row) in enumerate(page_data.iterrows()):
            menu = row['대표메뉴'] if pd.notna(row['대표메뉴']) else "-"
            google_url = make_google_link(row)
            st.markdown(f"| {start_idx + i + 1} | **{row['상호']}** | {menu} | [⭐ 평점/리뷰 확인하기]({google_url}) |")
    else:
        st.warning("조건에 맞는 식당이 없습니다.")
else:
    st.error("파일은 존재하지만 데이터를 읽어오지 못했습니다. CSV 파일 내부의 컬럼명('식당명', '지역명')을 다시 확인해주세요.")

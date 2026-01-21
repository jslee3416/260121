import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 평점 파인더", layout="wide")

@st.cache_data
def load_and_clean_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            st.error(f"파일을 찾을 수 없습니다: {file_name}")
            return pd.DataFrame()
        
        # 인코딩 및 자동 구분자 감지
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

        # [서울관광재단 데이터 컬럼 매칭]
        # 식당명 -> 상호, 지역명 -> 지역, 대표메뉴명 -> 메뉴
        name_map = {
            '식당명': '상호',
            '지역명': '지역',
            '대표메뉴명': '대표메뉴',
            '영업시간내용': '영업시간',
            '홈페이지(URL)': '홈페이지'
        }
        
        # 존재하는 컬럼만 선택하여 이름 변경
        existing_cols = [c for c in name_map.keys() if c in df.columns]
        df = df[existing_cols].rename(columns=name_map)
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return pd.DataFrame()

# 데이터 로드
DATA_FILE = "restaurants.csv"
df = load_and_clean_data(DATA_FILE)

# 2. 메인 UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.markdown("서울관광재단 인증 맛집 리스트입니다. **식당 이름을 클릭**하면 구글 맵 평점을 바로 확인할 수 있습니다.")

if not df.empty:
    # 사이드바 지역 필터
    st.sidebar.header("📍 지역 필터")
    area_list = sorted(df['지역'].dropna().unique())
    selected_area = st.sidebar.selectbox("지역을 선택하세요", ["전체"] + area_list)
    
    # 데이터 필터링
    if selected_area != "전체":
        filtered_df = df[df['지역'] == selected_area]
    else:
        filtered_df = df

    # 검색 기능 추가
    search_query = st.text_input("🔍 찾으시는 식당 이름이 있나요?", "")
    if search_query:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_query, na=False)]

    # 3. 구글 맵 검색 링크 생성 함수
    def make_google_link(row):
        # "지역명 + 식당명"으로 검색 정확도 극대화
        query = urllib.parse.quote(f"{row['지역']} {row['상호']}")
        return f"https://www.google.com/maps/search/{query}"

    # 결과 데이터 가공
    results = filtered_df.copy()
    results['구글맵 평점확인'] = results.apply(make_google_link, axis=1)

    # 4. 리스트 출력 (페이지네이션)
    rows_per_page = 20
    total_pages = max(len(results) // rows_per_page + (1 if len(results) % rows_per_page > 0 else 0), 1)
    
    col_page, col_info = st.columns([1, 4])
    with col_page:
        current_page = st.number_input(f"페이지 (총 {total_pages}P)", 1, total_pages, 1)
    with col_info:
        st.write(f"검색 결과: 총 **{len(results)}**개의 식당")

    start_idx = (current_page - 1) * rows_per_page
    page_data = results.iloc[start_idx : start_idx + rows_per_page]

    # 표 출력 (Markdown을 활용해 클릭 가능한 링크 생성)
    st.markdown("---")
    
    # 테이블 헤더
    header = "| 식당명 | 지역 | 대표메뉴 | 실시간 구글 평점 링크 |"
    sep = "| :--- | :--- | :--- | :--- |"
    rows = []
    
    for _, row in page_data.iterrows():
        menu = row['대표메뉴'] if '대표메뉴' in row and pd.notna(row['대표메뉴']) else "-"
        link_text = f"[⭐ 평점/리뷰 확인하기]({row['구글맵 평점확인']})"
        rows.append(f"| **{row['상호']}** | {row['지역']} | {menu} | {link_text} |")

    st.markdown(header + "\n" + sep + "\n" + "\n".join(rows), unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다. 파일명과 GitHub 업로드 상태를 확인해 주세요.")

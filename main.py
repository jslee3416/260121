import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 레이아웃 및 제목 설정
st.set_page_config(page_title="서울 맛집 구글 평점 파인더", layout="wide")

@st.cache_data
def load_and_clean_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        # 인코딩 처리 (CP949, UTF-8 순차 시도)
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

        # [컬럼 매칭] 서울관광재단 데이터 기준
        name_map = {
            '식당명': '상호',
            '지역명': '지역',
            '대표메뉴명': '대표메뉴'
        }
        
        # 존재하는 컬럼만 선택하여 이름 변경
        existing_cols = [c for c in name_map.keys() if c in df.columns]
        df = df[existing_cols].rename(columns=name_map)
        
        # [행정구역 분리] '지역' 컬럼에서 구와 동 추출
        # 예: "강남구 역삼동" -> 구: 강남구, 동: 역삼동
        def split_region(x):
            if pd.isna(x): return "미분류", "미분류"
            parts = str(x).split()
            gu = parts[0] if len(parts) > 0 else "미분류"
            dong = parts[1] if len(parts) > 1 else "전체"
            return gu, dong

        df[['구', '동']] = df['지역'].apply(lambda x: pd.Series(split_region(x)))
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return pd.DataFrame()

# 요청하신 대로 데이터 파일명 수정
DATA_FILE = "restaurants.csv"
df = load_and_clean_data(DATA_FILE)

# 2. 메인 UI 구성
st.title("🍴 서울 맛집 실시간 평점 탐색기")
st.markdown("---")

if not df.empty:
    # --- 사이드바: 행정구역 필터 ---
    st.sidebar.header("📍 지역 필터")
    
    # 구 선택
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    # 선택된 구에 해당하는 동 리스트 생성
    dong_options = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", ["전체"] + dong_options)
    
    # 필터링 로직
    if selected_dong == "전체":
        filtered_df = df[df['구'] == selected_gu]
    else:
        filtered_df = df[(df['구'] == selected_gu) & (df['동'] == selected_dong)]

    # 키워드 검색
    search_query = st.sidebar.text_input("🔍 식당 이름 검색", "")
    if search_query:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_query, na=False)]

    # --- 메인 결과 출력 ---
    st.subheader(f"📍 {selected_gu} {selected_dong if selected_dong != '전체' else ''} 맛집 목록")
    st.info(f"선택 지역 식당: **{len(filtered_df)}개** (식당명을 클릭하면 구글 맵 평점으로 연결됩니다)")

    if not filtered_df.empty:
        # 페이지네이션 (15개씩)
        rows_per_page = 15
        total_pages = max(len(filtered_df) // rows_per_page + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
        
        col_page, _ = st.columns([1, 4])
        with col_page:
            current_page = st.number_input(f"페이지 (1/{total_pages})", 1, total_pages, 1)
        
        start_idx = (current_page - 1) * rows_per_page
        page_data = filtered_df.iloc[start_idx : start_idx + rows_per_page].copy()

        # 구글 맵 검색 링크 생성 함수
        def make_google_link(row):
            # 정확한 검색을 위해 구+동+상호 조합
            query = urllib.parse.quote(f"{row['구']} {row['동']} {row['상호']}")
            return f"https://www.google.com/maps/search/{query}"

        # 표 출력
        st.markdown("---")
        header = "| 번호 | 식당명 | 대표메뉴 | 구글 맵 실시간 평점 |"
        sep = "| :--- | :--- | :--- | :--- |"
        rows = []
        
        for i, (_, row) in enumerate(page_data.iterrows()):
            menu = row['대표메뉴'] if pd.notna(row['대표메뉴']) else "-"
            google_url = make_google_link(row)
            link_text = f"[⭐ 평점/리뷰 확인하기]({google_url})"
            rows.append(f"| {start_idx + i + 1} | **{row['상호']}** | {menu} | {link_text} |")

        st.markdown(header + "\n" + sep + "\n" + "\n".join(rows))
    else:
        st.warning("선택하신 조건에 맞는 식당이 없습니다.")

else:
    st.error(f"'{DATA_FILE}' 파일을 불러올 수 없습니다.")
    st.markdown("""
    ### 🛠️ 해결 방법
    1. GitHub 저장소에 파일 이름이 **`restaurants.csv`**인지 확인하세요.
    2. 파일 내용에 '식당명', '지역명' 컬럼이 포함되어 있는지 확인하세요.
    """)

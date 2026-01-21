import streamlit as st
import pandas as pd
import urllib.parse
import os

st.set_page_config(page_title="서울 맛집 파인더", layout="wide")

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()

        # 1. 모든 인코딩 수단 동원
        df = None
        for enc in ['cp949', 'utf-8-sig', 'euc-kr', 'utf-8']:
            try:
                # engine='c'를 사용하여 더 빠르게 읽고, 오류가 있는 줄은 건너뜁니다.
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty:
                    break
            except:
                continue
        
        if df is None: return pd.DataFrame()

        # [진단] 현재 읽어온 컬럼명을 사이드바에 출력 (사용자 확인용)
        raw_cols = df.columns.tolist()
        st.sidebar.write("🔍 감지된 컬럼명:", raw_cols)

        # 2. [강제 매칭 로직] 이름이 달라도 순서로 가져오기
        # 보통 '식당명'은 1~2번째, '지역명'은 4~5번째에 위치합니다.
        # 이름으로 먼저 찾아보고, 못 찾으면 인덱스(순서)로 가져옵니다.
        
        name_col = next((c for c in df.columns if '식당명' in str(c)), df.columns[1])
        area_col = next((c for c in df.columns if '지역명' in str(c)), df.columns[3] if len(df.columns) > 3 else df.columns[-1])

        # 슬림화: 딱 두 가지만 추출
        new_df = df[[name_col, area_col]].copy()
        new_df.columns = ['상호', '지역']
        
        # '구' 정보 추출 (첫 단어)
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "미분류")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
        
    except Exception as e:
        st.sidebar.error(f"진단 오류: {e}")
        return pd.DataFrame()

df = load_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")

if not df.empty:
    st.sidebar.success("✅ 데이터를 불러왔습니다!")
    
    # 지역 필터
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", ["전체"] + gu_list)
    
    filtered_df = df if selected_gu == "전체" else df[df['구'] == selected_gu]

    # 검색바
    search_q = st.sidebar.text_input("🔍 식당 이름 검색", "")
    if search_q:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_q, na=False)]

    st.subheader(f"📍 {selected_gu} 지역 식당 목록")
    
    # 테이블 출력
    if not filtered_df.empty:
        rows_per_page = 20
        total_pages = max(len(filtered_df) // rows_per_page + 1, 1)
        current_page = st.number_input(f"페이지 (1/{total_pages})", 1, total_pages, 1)
        
        start_idx = (current_page - 1) * rows_per_page
        page_data = filtered_df.iloc[start_idx : start_idx + rows_per_page]

        st.markdown("---")
        st.markdown("| 번호 | 식당명 | 상세 주소 | 구글 평점 연결 |")
        st.markdown("| :--- | :--- | :--- | :--- |")
        
        for i, (_, row) in enumerate(page_data.iterrows()):
            # 구글 검색 링크 생성
            search_text = f"{row['지역']} {row['상호']}"
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_text + ' 평점')}"
            
            st.markdown(f"| {start_idx + i + 1} | **{row['상호']}** | {row['지역']} | [⭐ 리뷰보기]({google_url}) |")
    else:
        st.info("조건에 맞는 결과가 없습니다.")
else:
    st.error("🚨 여전히 데이터를 읽지 못하고 있습니다.")
    st.markdown("""
    **확인해 주세요:**
    1. GitHub의 `restaurants.csv` 파일을 클릭했을 때 데이터가 표 형태로 잘 보이나요?
    2. 파일 용량이 너무 크면(25MB 이상) GitHub에서 읽지 못할 수 있습니다.
    3. 메모장으로 파일을 열어 **첫 번째 줄**이 어떻게 시작하는지 알려주시면 즉시 고쳐드릴 수 있습니다.
    """)

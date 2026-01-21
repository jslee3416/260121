import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정 및 프리미엄 스타일 정의
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    
    .stApp { background-color: #ffffff; }
    
    .header-section {
        text-align: center;
        padding: 60px 0 40px 0;
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.2rem;
        color: #111;
        letter-spacing: -1px;
    }
    .sub-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        color: #999;
        font-size: 1.1rem;
        margin-bottom: 50px;
    }

    /* 그리드 레이아웃: 한 줄에 여러 개 배치 */
    .restaurant-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 30px;
        padding: 40px 0;
    }

    .res-card {
        border-bottom: 1px solid #eee;
        padding: 25px 15px;
        transition: all 0.3s;
    }
    .res-card:hover {
        background-color: #fdfdfd;
        border-bottom: 1px solid #1a1a1a;
    }
    .res-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.6rem;
        color: #1a1a1a;
        margin-bottom: 8px;
    }
    .res-addr {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #888;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* 구글 평점 연결 버튼 */
    .btn-link {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 10px 22px;
        text-decoration: none;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .btn-link:hover {
        background-color: #1a1a1a;
        color: #fff !important;
    }

    /* 행정구역 버튼 스타일 */
    div.stButton > button {
        border-radius: 0px;
        border: 1px solid #f0f0f0;
        background-color: white;
        font-size: 0.8rem;
        color: #777;
        width: 100%;
        margin-bottom: 5px;
    }
    div.stButton > button:hover {
        border-color: #1a1a1a;
        color: #1a1a1a;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 로직 (2번 열: 식당명, 4번 열: 지역명)
@st.cache_data
def load_gourmet_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8']:
            try:
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty: break
            except: continue
        
        if df is None: return pd.DataFrame()

        # [요청 반영] 
        # 2번째 열(index 1) = 식당명 (구글맵 연동 및 화면 표기)
        # 4번째 열(index 3) = 지역명 (행정구역 선택 기준)
        name_idx = 1
        area_idx = 3 # 4번째 열
        
        clean_df = pd.DataFrame({
            '상호': df.iloc[:, name_idx],
            '지역': df.iloc[:, area_idx]
        })
        
        # 행정구역(구) 추출: 지역명 컬럼의 첫 단어를 사용
        clean_df['구'] = clean_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return clean_df.dropna(subset=['상호']).reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_gourmet_data("restaurants.csv")

# 3. 화면 레이아웃
st.markdown("""
    <div class='header-section'>
        <div class='main-title'>SEOUL GOURMET</div>
        <div class='sub-title'>Essential Dining Guide for Connoisseurs</div>
    </div>
    """, unsafe_allow_html=True)

if not df.empty:
    # 4. 행정구역 선택 버튼 (가로형 배치)
    gu_list = sorted(df['구'].unique())
    
    cols = st.columns(8) # 8열 배치
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    for i, gu in enumerate(gu_list):
        with cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    # 5. 리스트 출력 (그리드 레이아웃)
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    st.markdown(f"<p style='margin-top:50px; font-weight:600; font-size:1.1rem; border-left: 3px solid #1a1a1a; padding-left:15px; letter-spacing:1px;'>{st.session_state.selected_gu} DISTRICT</p>", unsafe_allow_html=True)
    
    grid_html = '<div class="restaurant-grid">'
    for _, row in display_df.iterrows():
        # 검색 쿼리: 식당명(2번 열) + 지역명(4번 열) 조합으로 구글맵 검색 정확도 향상
        query_text = f"{row['지역']} {row['상호']} 평점"
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(query_text)}"
        
        grid_html += f"""
            <div class="res-card">
                <div class="res-name">{row['상호']}</div>
                <div class="res-addr">{row['지역']}</div>
                <a href="{google_url}" target="_blank" class="btn-link">Explore Ratings</a>
            </div>
        """
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다. GitHub의 restaurants.csv 파일 구성을 확인해주세요.")

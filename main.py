import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정 (넓은 화면 사용)
st.set_page_config(page_title="SEOUL GOURMET", layout="wide")

# 고급스러운 콤팩트 UI 디자인 (CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    
    .stApp { background-color: #ffffff; }
    
    .header-section {
        text-align: center;
        padding: 40px 0;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 30px;
    }
    
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        color: #111;
        letter-spacing: -1px;
    }

    /* 그리드 레이아웃: 한 줄에 여러 개 표시하여 스크롤 단축 */
    .restaurant-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 25px;
        padding: 20px 0;
    }

    .res-card {
        border: 1px solid #eeeeee;
        padding: 25px;
        border-radius: 0px; /* 미니멀한 직각 디자인 */
        transition: all 0.3s ease;
        background: #fff;
    }
    
    .res-card:hover {
        border-color: #1a1a1a;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }

    .res-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        color: #1a1a1a;
        margin-bottom: 8px;
    }

    .res-addr {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #999;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
        line-height: 1.4;
    }

    .btn-link {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 10px 20px;
        text-decoration: none;
        font-size: 0.7rem;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: 0.3s;
    }
    
    .btn-link:hover {
        background-color: #1a1a1a;
        color: #ffffff !important;
    }

    /* 구 선택 버튼 스타일 */
    div.stButton > button {
        border-radius: 0px;
        border: 1px solid #eee;
        background-color: white;
        color: #666;
        width: 100%;
        font-size: 0.8rem;
    }
    div.stButton > button:hover {
        border-color: #1a1a1a;
        color: #1a1a1a;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로딩 (인덱스 기반 안정화 버전)
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

        # 위치 기반 추출: 2번째 컬럼(상호), 5번째(지역)
        name_idx = 1
        area_idx = 4 if len(df.columns) > 4 else (len(df.columns) - 1)
        
        new_df = pd.DataFrame({
            '상호': df.iloc[:, name_idx],
            '지역': df.iloc[:, area_idx]
        })
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_gourmet_data("restaurants.csv")

# 3. 상단 헤더
st.markdown("<div class='header-section'><div class='main-title'>SEOUL GOURMET</div></div>", unsafe_allow_html=True)

if not df.empty:
    # 4. 행정구역 선택 버튼 (가로 배치)
    gu_list = sorted(df['구'].unique())
    
    st.markdown("<p style='text-align:center; font-size:0.7rem; letter-spacing:2px; color:#bbb; margin-bottom:15px;'>SELECT DISTRICT</p>", unsafe_allow_html=True)
    
    # 구 버튼을 8열씩 배치하여 화면 공간 절약
    cols = st.columns(8)
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    for i, gu in enumerate(gu_list[:16]): # 주요 16개 구 버튼 생성
        with cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    # 5. 그리드 레이아웃 출력 (카드형)
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    st.markdown(f"<p style='margin-top:40px; font-size:0.9rem; font-weight:bold;'>{st.session_state.selected_gu} EXPLORATION</p>", unsafe_allow_html=True)
    
    # HTML 그리드 생성
    grid_html = '<div class="restaurant-grid">'
    for _, row in display_df.iterrows():
        # 검색 쿼리: 지역 + 상호 + 평점
        query = urllib.parse.quote(f"{row['지역']} {row['상호']} 평점")
        google_url = f"https://www.google.com/search?q={query}"
        
        grid_html += f"""
            <div class="res-card">
                <div class="res-name">{row['상호']}</div>
                <div class="res-addr">{row['지역']}</div>
                <a href="{google_url}" target="_blank" class="btn-link">Check Ratings & Reviews</a>
            </div>
        """
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)

else:
    st.error("데이터를 불러올 수 없습니다. 파일명을 확인해 주세요.")

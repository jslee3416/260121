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
    
    /* 헤더 스타일 */
    .header-section {
        text-align: center;
        padding: 60px 0 40px 0;
        background: #fff;
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.2rem;
        color: #111;
        letter-spacing: -1px;
        margin-bottom: 10px;
    }
    .sub-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        color: #999;
        font-size: 1.1rem;
        margin-bottom: 50px;
    }

    /* 행정구역 버튼 컨테이너 */
    .filter-label {
        text-align: center;
        font-size: 0.7rem;
        letter-spacing: 2px;
        color: #bbb;
        margin-bottom: 20px;
        text-transform: uppercase;
    }

    /* 그리드 레이아웃: 스크롤 최소화 */
    .restaurant-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 30px;
        padding: 40px 0;
    }

    /* 카드 디자인 */
    .res-card {
        border-bottom: 1px solid #eee;
        padding: 20px 10px;
        transition: all 0.3s;
    }
    .res-card:hover {
        background-color: #fafafa;
    }
    .res-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        color: #1a1a1a;
        margin-bottom: 8px;
    }
    .res-addr {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #999;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* 버튼 스타일 */
    .btn-link {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 8px 20px;
        text-decoration: none;
        font-size: 0.7rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .btn-link:hover {
        background-color: #1a1a1a;
        color: #fff !important;
    }

    /* 스트림릿 버튼 커스텀 */
    div.stButton > button {
        border-radius: 0px;
        border: 1px solid #eee;
        background-color: white;
        font-size: 0.8rem;
        padding: 5px 10px;
        color: #888;
    }
    div.stButton > button:active, div.stButton > button:focus {
        border-color: #1a1a1a !important;
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 로직
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

        # [반영] 2번째 컬럼(index 1) = 식당명, 5번째 컬럼(index 4) = 지역명
        name_idx = 1
        area_idx = 4 if len(df.columns) > 4 else (len(df.columns) - 1)
        
        # 슬림하게 필요한 데이터만 추출
        clean_df = pd.DataFrame({
            '상호': df.iloc[:, name_idx],
            '지역': df.iloc[:, area_idx]
        })
        
        # '구' 정보 추출
        clean_df['구'] = clean_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return clean_df.dropna(subset=['상호']).reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_gourmet_data("restaurants.csv")

# 3. 메인 화면 구성
st.markdown("""
    <div class='header-section'>
        <div class='main-title'>SEOUL GOURMET</div>
        <div class='sub-title'>Essential Dining Guide for Connoisseurs</div>
    </div>
    """, unsafe_allow_html=True)

if not df.empty:
    # 4. 행정구역 선택 버튼 (가로형)
    gu_list = sorted(df['구'].unique())
    st.markdown("<div class='filter-label'>Select District</div>", unsafe_allow_html=True)
    
    # 버튼 배치를 위한 컬럼 생성 (8개씩 배치)
    cols = st.columns(8)
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    for i, gu in enumerate(gu_list[:24]): # 최대 24개 구까지 버튼 표시
        with cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    # 5. 리스트 출력 (그리드 레이아웃)
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    st.markdown(f"<p style='margin-top:50px; font-weight:600; font-size:1.1rem; border-left: 3px solid #1a1a1a; padding-left:15px;'>{st.session_state.selected_gu}</p>", unsafe_allow_html=True)
    
    grid_html = '<div class="restaurant-grid">'
    for _, row in display_df.iterrows():
        # 구글 검색 쿼리
        query = urllib.parse.quote(f"{row['지역']} {row['상호']} 평점")
        google_url = f"https://www.google.com/search?q={query}"
        
        grid_html += f"""
            <div class="res-card">
                <div class="res-name">{row['상호']}</div>
                <div class="res-addr">{row['지역']}</div>
                <a href="{google_url}" target="_blank" class="btn-link">Check Reviews</a>
            </div>
        """
    grid_html += '</div>'
    
    st.markdown(grid_html, unsafe_allow_html=True)

else:
    st.error("The gourmet database could not be reached. Please verify 'restaurants.csv'.")

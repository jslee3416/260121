import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정 및 다크 테마 감성 적용
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# CSS를 통한 고급스러운 UI 커스텀
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');
    
    .main {
        background-color: #ffffff;
    }
    .stTitle {
        font-family: 'Playfair Display', serif;
        font-size: 3rem !important;
        color: #1a1a1a;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        text-align: center;
        color: #757575;
        margin-bottom: 3rem;
    }
    .restaurant-card {
        border-bottom: 1px solid #e0e0e0;
        padding: 40px 20px;
        transition: all 0.3s ease;
    }
    .restaurant-card:hover {
        background-color: #fcfcfc;
    }
    .restaurant-name {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        color: #111;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    .restaurant-location {
        font-size: 0.9rem;
        color: #888;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 25px;
    }
    .btn-google {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 12px 25px;
        text-decoration: none;
        font-size: 0.8rem;
        letter-spacing: 2px;
        transition: all 0.3s;
    }
    .btn-google:hover {
        background-color: #1a1a1a;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        if not os.path.exists(file_path): return pd.DataFrame()

        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8']:
            try:
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty: break
            except: continue
        
        if df is None: return pd.DataFrame()

        # 순서 기반 추출: 1번(식당명), 4번 내외(지역명)
        name_col = df.columns[1]
        area_col = next((c for c in df.columns if '지역' in str(c) or '주소' in str(c)), df.columns[-1])

        new_df = df[[name_col, area_col]].copy()
        new_df.columns = ['상호', '지역']
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "SEOUL")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
    except:
        return pd.DataFrame()

df = load_data(DATA_FILE)

# 2. UI 구성
st.markdown("<h1 class='stTitle'>SEOUL GOURMET</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>A Curated Selection of the City's Finest Dining</p>", unsafe_allow_html=True)

if not df.empty:
    # 사이드바 디자인
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("SELECT DISTRICT", gu_list)
    
    # 해당 구 상위 20개
    filtered_df = df[df['구'] == selected_gu].head(20)

    # 3. 고급스러운 리스트 출력 (이미지 삭제, 텍스트 중심)
    for i, row in filtered_df.iterrows():
        search_query = f"{row['지역']} {row['상호']} 평점"
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        
        st.markdown(f"""
            <div class="restaurant-card">
                <div class="restaurant-location">{row['지역']}</div>
                <div class="restaurant-name">{row['상호']}</div>
                <div style="margin-top: 20px;">
                    <a href="{google_url}" target="_blank" class="btn-google">
                        EXPLORE REVIEWS & RATING
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("Unable to load the gourmet database.")

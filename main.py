import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정 및 프리미엄 스타일 적용
st.set_page_config(page_title="SEOUL GOURMET", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');
    
    .stApp { background-color: #ffffff; }
    
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        color: #111111;
        text-align: center;
        margin-top: 2rem;
        letter-spacing: -1px;
    }
    .sub-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        text-align: center;
        color: #888888;
        margin-bottom: 4rem;
        font-size: 1.1rem;
    }
    .restaurant-card {
        border-bottom: 1px solid #eeeeee;
        padding: 50px 0;
        max-width: 800px;
        margin: 0 auto;
        text-align: center;
    }
    .location-tag {
        font-size: 0.8rem;
        color: #b59d5f; /* 골드 톤 포인트 */
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 15px;
    }
    .restaurant-name {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        color: #1a1a1a;
        margin-bottom: 25px;
    }
    .btn-explore {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 12px 30px;
        text-decoration: none;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        transition: 0.4s;
        text-transform: uppercase;
    }
    .btn-explore:hover {
        background-color: #1a1a1a;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_gourmet_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()

        # [안정화 로직] 인코딩 및 엔진 설정 강화
        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                # low_memory=False로 타입 추론 오류 방지
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty:
                    # 컬럼명 앞뒤 공백 제거 및 문자열 변환
                    df.columns = [str(c).strip() for c in df.columns]
                    break
            except:
                continue
        
        if df is None or df.empty:
            return pd.DataFrame()

        # [위치 기반 매칭] 2번째 컬럼(식당명), 4번째 혹은 마지막(지역명)
        # 만약 컬럼이 부족하면 에러 없이 안전하게 인덱스 조절
        name_idx = 1 if len(df.columns) > 1 else 0
        area_idx = 4 if len(df.columns) > 4 else (len(df.columns) - 1)
        
        new_df = pd.DataFrame({
            '상호': df.iloc[:, name_idx],
            '지역': df.iloc[:, area_idx]
        })
        
        # '구' 추출 로직
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "SEOUL")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
    except Exception as e:
        st.sidebar.error(f"System Load Error: {e}")
        return pd.DataFrame()

# 데이터 로드
df = load_gourmet_data(DATA_FILE)

# 2. 메인 UI 출력
st.markdown("<div class='main-title'>SEOUL GOURMET</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Fine Dining & Exceptional Taste</div>", unsafe_allow_html=True)

if not df.empty:
    # 사이드바: DISTRICT SELECTOR
    st.sidebar.markdown("<p style='letter-spacing:2px; font-size:0.8rem; color:#888;'>CHOOSE DISTRICT</p>", unsafe_allow_html=True)
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("", gu_list, label_visibility="collapsed")
    
    # 해당 구 상위 20개 리스팅
    filtered_df = df[df['구'] == selected_gu].head(20)

    # 3. 고급스러운 리스트 출력 (미니멀 텍스트 중심)
    for _, row in filtered_df.iterrows():
        # 검색 쿼리: 주소 + 상호 + 평점
        search_query = f"{row['지역']} {row['상호']} 평점"
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
        
        st.markdown(f"""
            <div class="restaurant-card">
                <div class="location-tag">{row['지역']}</div>
                <div class="restaurant-name">{row['상호']}</div>
                <a href="{google_url}" target="_blank" class="btn-explore">
                    View Ratings & Reviews
                </a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("The gourmet database is currently unavailable.")
    st.info("Check if 'restaurants.csv' exists in the repository.")

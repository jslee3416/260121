import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# 2. CSS 스타일 (고급스러운 그리드 레이아웃)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    .stApp { background-color: #ffffff; }
    .header-section { text-align: center; padding: 40px 0; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #111; letter-spacing: -1px; }
    
    /* 그리드 시스템 핵심 */
    .restaurant-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 25px;
        padding: 20px 0;
    }
    .res-card {
        border: 1px solid #eee;
        padding: 25px;
        background: #fff;
        transition: 0.3s;
        text-align: left;
    }
    .res-card:hover { border-color: #1a1a1a; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
    .res-name { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a1a1a; margin-bottom: 8px; }
    .res-addr { font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #999; margin-bottom: 20px; }
    .btn-link {
        display: inline-block;
        border: 1px solid #1a1a1a;
        color: #1a1a1a;
        padding: 8px 18px;
        text-decoration: none;
        font-size: 0.7rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .btn-link:hover { background-color: #1a1a1a; color: #fff !important; }
    
    /* 버튼 스타일 */
    div.stButton > button { border-radius: 0; border: 1px solid #eee; background: white; color: #777; width: 100%; }
    div.stButton > button:hover { border-color: #1a1a1a; color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩
@st.cache_data
def load_data(file_name):
    try:
        path = os.path.join(os.path.dirname(__file__), file_name)
        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8']:
            try:
                df = pd.read_csv(path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None: break
            except: continue
        
        if df is not None:
            # 2번 열: 식당명, 4번 열: 지역명 (0부터 시작하므로 1과 3)
            new_df = pd.DataFrame({
                '상호': df.iloc[:, 1],
                '지역': df.iloc[:, 3]
            })
            new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
            return new_df.dropna(subset=['상호']).reset_index(drop=True)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df = load_data("restaurants.csv")

# 4. 화면 구성
st.markdown("<div class='header-section'><div class='main-title'>SEOUL GOURMET</div></div>", unsafe_allow_html=True)

if not df.empty:
    gu_list = sorted(df['구'].unique())
    cols = st.columns(8)
    
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    for i, gu in enumerate(gu_list[:24]):
        with cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    # 필터링
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    # 5. 그리드 생성 (이 부분이 중요합니다)
    grid_html = '<div class="restaurant-grid">'
    for _, row in display_df.iterrows():
        query = urllib.parse.quote(f"{row['지역']} {row['상호']} 평점")
        google_url = f"https://www.google.com/search?q={query}"
        
        # 각 식당 카드를 문자열로 누적
        grid_html += f"""
            <div class="res-card">
                <div class="res-name">{row['상호']}</div>
                <div class="res-addr">{row['지역']}</div>
                <a href="{google_url}" target="_blank" class="btn-link">Explore Ratings</a>
            </div>
        """
    grid_html += '</div>'
    
    # 최종적으로 한 번만 렌더링
    st.markdown(grid_html, unsafe_allow_html=True)
else:
    st.error("데이터 파일 'restaurants.csv'를 찾을 수 없거나 형식이 잘못되었습니다.")

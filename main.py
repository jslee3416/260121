import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# 스타일 설정 (버튼 및 텍스트 가독성)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    .main-title { font-family: 'Playfair Display', serif; font-size: 3.5rem; text-align: center; margin-bottom: 40px; }
    .stButton>button { width: 100%; border-radius: 0; border: 1px solid #eee; background: white; }
    .stButton>button:hover { border-color: #1a1a1a; color: #1a1a1a; }
    /* 카드 가이드 텍스트 */
    .res-label { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: bold; margin-bottom: 5px; }
    .addr-label { color: #888; font-size: 0.85rem; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로딩 (2번 열: 식당명, 4번 열: 지역명)
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    path = os.path.join(os.path.dirname(__file__), file_name)
    
    if not os.path.exists(path):
        return pd.DataFrame()

    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines='skip', engine='python')
            if df is not None:
                # 2번 열(index 1): 상호, 4번 열(index 3): 지역명
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str),
                    '지역': df.iloc[:, 3].astype(str)
                })
                res_df['구'] = res_df['지역'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "미분류")
                return res_df.dropna(subset=['상호']).reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 화면 구성
st.markdown("<div class='main-title'>SEOUL GOURMET</div>", unsafe_allow_html=True)

if not df.empty:
    # 행정구역 선택 버튼 (8열 배치)
    gu_list = sorted(df['구'].unique())
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    gu_cols = st.columns(8)
    for i, gu in enumerate(gu_list[:24]):
        with gu_cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    st.divider()
    st.subheader(f"📍 {st.session_state.selected_gu} Best Selection")

    # 4. 그리드 레이아웃 (HTML 대신 Streamlit Column 활용)
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    # 한 줄에 3개씩 배치 (스크롤 단축)
    rows = [display_df.iloc[i:i+3] for i in range(0, len(display_df), 3)]
    
    for row_data in rows:
        cols = st.columns(3)
        for i, (idx, item) in enumerate(row_data.iterrows()):
            with cols[i]:
                # 카드 내부 디자인
                st.markdown(f"<div class='res-label'>{item['상호']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='addr-label'>{item['지역']}</div>", unsafe_allow_html=True)
                
                # 구글 평점 버튼
                query = urllib.parse.quote(f"{item['지역']} {item['상호']} 평점")
                google_url = f"https://www.google.com/search?q={query}"
                st.link_button("EXPLORE RATINGS", google_url, use_container_width=True)
                st.write("") # 간격 조절
else:
    st.error("데이터를 불러올 수 없습니다. 'restaurants.csv' 파일을 확인해주세요.")

import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# CSS 스타일 (그리드 레이아웃)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    .stApp { background-color: #ffffff; }
    .header-section { text-align: center; padding: 40px 0; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; color: #111; letter-spacing: -1px; }
    .restaurant-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; padding: 20px 0; }
    .res-card { border: 1px solid #eee; padding: 25px; background: #fff; transition: 0.3s; text-align: left; }
    .res-card:hover { border-color: #1a1a1a; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
    .res-name { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a1a1a; margin-bottom: 8px; }
    .res-addr { font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #999; margin-bottom: 20px; }
    .btn-link { display: inline-block; border: 1px solid #1a1a1a; color: #1a1a1a; padding: 8px 18px; text-decoration: none; font-size: 0.7rem; letter-spacing: 1px; text-transform: uppercase; }
    .btn-link:hover { background-color: #1a1a1a; color: #fff !important; }
    div.stButton > button { border-radius: 0; border: 1px solid #eee; background: white; color: #777; width: 100%; margin-bottom:5px; }
    div.stButton > button:hover { border-color: #1a1a1a; color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로딩 (강력한 경로 확인 및 인코딩 대응)
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    # 현재 실행 파일의 위치를 기준으로 파일 찾기
    possible_paths = [
        file_name,
        os.path.join(os.getcwd(), file_name),
        os.path.join(os.path.dirname(__file__), file_name) if '__file__' in locals() else file_name
    ]
    
    df = None
    target_path = ""
    
    for path in possible_paths:
        if os.path.exists(path):
            target_path = path
            break
            
    if not target_path:
        return pd.DataFrame(), "파일을 찾을 수 없습니다. (restaurants.csv)"

    # 다양한 인코딩으로 시도
    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr', 'latin1']:
        try:
            # 엔진을 'python'으로 설정하여 더 유연하게 읽기
            df = pd.read_csv(target_path, encoding=enc, on_bad_lines='skip', engine='python')
            if df is not None and not df.empty:
                break
        except:
            continue
            
    if df is not None and not df.empty:
        try:
            # 요청하신 컬럼 위치: 2번(index 1) 식당명, 4번(index 3) 지역명
            new_df = pd.DataFrame({
                '상호': df.iloc[:, 1].astype(str),
                '지역': df.iloc[:, 3].astype(str)
            })
            new_df['구'] = new_df['지역'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "미분류")
            return new_df.dropna(subset=['상호']).reset_index(drop=True), "성공"
        except Exception as e:
            return pd.DataFrame(), f"컬럼 구조 오류: {str(e)}"
            
    return pd.DataFrame(), "데이터를 읽을 수 없습니다. (인코딩/형식 오류)"

df, status_msg = load_data()

# 3. 화면 구성
st.markdown("<div class='header-section'><div class='main-title'>SEOUL GOURMET</div></div>", unsafe_allow_html=True)

if not df.empty:
    gu_list = sorted(df['구'].unique())
    # 구 버튼 배치
    cols = st.columns(8)
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    for i, gu in enumerate(gu_list[:24]): # 최대 24개 버튼
        with cols[i % 8]:
            if st.button(gu):
                st.session_state.selected_gu = gu

    # 필터링 및 출력
    display_df = df[df['구'] == st.session_state.selected_gu].head(20)
    
    grid_html = '<div class="restaurant-grid">'
    for _, row in display_df.iterrows():
        query = urllib.parse.quote(f"{row['지역']} {row['상호']} 평점")
        google_url = f"https://www.google.com/search?q={query}"
        
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
    st.error(f"🚨 에러 발생: {status_msg}")
    st.info("GitHub 저장소 메인 폴더에 'restaurants.csv' 파일이 정확히 있는지 확인해주세요.")

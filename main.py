import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정 (넓은 화면 사용)
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# CSS 스타일: 텍스트 크기와 버튼 디자인만 미니멀하게 조정
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500&display=swap');
    .main-title { font-family: 'Playfair Display', serif; font-size: 3rem; text-align: center; margin: 30px 0; color: #111; }
    .res-name { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: bold; color: #1a1a1a; margin-bottom: 5px; }
    .res-addr { font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #888; margin-bottom: 10px; }
    /* 버튼 스타일 통일 */
    .stButton>button { border-radius: 0; border: 1px solid #eee; background: white; width: 100%; }
    .stButton>button:hover { border-color: #1a1a1a; color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로딩 (2번 열: 식당명, 4번 열: 지역명)
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    # 파일 경로 탐색
    path = os.path.join(os.path.dirname(__file__), file_name) if '__file__' in locals() else file_name
    
    if not os.path.exists(path):
        return pd.DataFrame()

    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(path, encoding=enc, on_bad_lines='skip', engine='python')
            if df is not None:
                # [반영] 2번째 열(Index 1): 상호, 4번째 열(Index 3): 지역명
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str),
                    '지역': df.iloc[:, 3].astype(str)
                })
                # '구' 추출 (지역명의 첫 단어)
                res_df['구'] = res_df['지역'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "미분류")
                return res_df.dropna(subset=['상호']).reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 상단 제목
st.markdown("<div class='main-title'>SEOUL GOURMET</div>", unsafe_allow_html=True)

if not df.empty:
    # 4. 행정구역 선택 버튼 (가로 8열 배치)
    gu_list = sorted(df['구'].unique())
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    st.write("📍 **Select District**")
    gu_cols = st.columns(8)
    for i, gu in enumerate(gu_list[:24]): # 최대 24개 구 표시
        with gu_cols[i % 8]:
            if st.button(gu, key=f"btn_{gu}"):
                st.session_state.selected_gu = gu

    st.divider()
    st.subheader(f"✨ {st.session_state.selected_gu} Selection")

    # 5. 그리드 레이아웃 (한 줄에 3개씩 배치하여 스크롤 단축)
    filtered_df = df[df['구'] == st.session_state.selected_gu].head(30) # 최대 30개 표시

    # 데이터프레임을 3개씩 묶어서 행(row) 생성
    for i in range(0, len(filtered_df), 3):
        cols = st.columns(3) # 가로 3칸 생성
        for j in range(3):
            if i + j < len(filtered_df):
                item = filtered_df.iloc[i + j]
                with cols[j]:
                    # 카드 형태 컨테이너
                    with st.container(border=True):
                        st.markdown(f"<div class='res-name'>{item['상호']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='res-addr'>{item['지역']}</div>", unsafe_allow_html=True)
                        
                        # 구글 검색 링크 생성 (식당명 + 구이름 조합)
                        query = urllib.parse.quote(f"{item['구']} {item['상호']} 평점")
                        google_url = f"https://www.google.com/search?q={query}"
                        
                        # 표준 링크 버튼 사용 (가장 안전함)
                        st.link_button("EXPLORE RATINGS", google_url, use_container_width=True)
else:
    st.error("데이터 파일 'restaurants.csv'를 읽어오지 못했습니다. 파일 위치와 형식을 다시 확인해 주세요.")

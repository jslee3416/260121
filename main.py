import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET", layout="wide")

# 2. 데이터 로딩 (2번 열: 식당명, 4번 열: 지역명)
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    if not os.path.exists(file_name):
        return pd.DataFrame()

    for enc in ['utf-8-sig', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv(file_name, encoding=enc, on_bad_lines='skip')
            if df is not None:
                # 2번 열(index 1): 상호 / 4번 열(index 3): 지역명
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str),
                    '지역': df.iloc[:, 3].astype(str)
                })
                # '구' 정보 추출
                res_df['구'] = res_df['지역'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "미분류")
                return res_df.dropna(subset=['상호']).reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 화면 출력
st.title("🍴 서울 맛집 리스트")

if not df.empty:
    # --- 행정구역 선택 버튼 (가로 배치) ---
    gu_list = sorted(df['구'].unique())
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    st.write("### 📍 지역 선택")
    # 버튼을 7개씩 가로로 배치
    gu_cols = st.columns(7)
    for i, gu in enumerate(gu_list):
        with gu_cols[i % 7]:
            if st.button(gu, use_container_width=True):
                st.session_state.selected_gu = gu

    st.divider()
    st.header(f"🔎 {st.session_state.selected_gu} 검색 결과")

    # --- 맛집 리스트 그리드 출력 (한 줄에 3개씩) ---
    filtered_df = df[df['구'] == st.session_state.selected_gu].head(30)
    
    # 데이터를 3개씩 끊어서 행 생성
    for i in range(0, len(filtered_df), 3):
        cols = st.columns(3) # 가로 3칸 생성
        for j in range(3):
            if i + j < len(filtered_df):
                item = filtered_df.iloc[i + j]
                with cols[j]:
                    # 개별 식당 정보 박스
                    with st.container(border=True):
                        st.subheader(item['상호'])
                        st.write(f"📍 {item['지역']}")
                        
                        # 구글 검색 링크 버튼
                        query = urllib.parse.quote(f"{item['지역']} {item['상호']} 평점")
                        url = f"https://www.google.com/search?q={url}"
                        st.link_button("⭐ 평점/리뷰 보기", f"https://www.google.com/search?q={query}", use_container_width=True)
else:
    st.error("데이터를 불러올 수 없습니다. 'restaurants.csv' 파일이 main.py와 같은 폴더에 있는지 확인해주세요.")

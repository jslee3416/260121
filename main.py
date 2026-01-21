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
                # '구' 정보 추출 (주소의 첫 단어)
                res_df['구'] = res_df['지역'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "미분류")
                return res_df.dropna(subset=['상호']).reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 화면 출력
st.title("🍴 서울 맛집 리스트")

if not df.empty:
    # --- 행정구역 선택 버튼 ---
    gu_list = sorted(df['구'].unique())
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    st.write("### 📍 지역 선택")
    gu_cols = st.columns(7)
    for i, gu in enumerate(gu_list):
        with gu_cols[i % 7]:
            if st.button(gu, use_container_width=True, key=f"gu_{gu}"):
                st.session_state.selected_gu = gu

    st.divider()
    st.header(f"🔎 {st.session_state.selected_gu} 검색 결과")

    # --- 맛집 리스트 그리드 출력 ---
    filtered_df = df[df['구'] == st.session_state.selected_gu].head(30)
    
    # 3개씩 끊어서 화면에 배치
    for i in range(0, len(filtered_df), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(filtered_df):
                item = filtered_df.iloc[i + j]
                with cols[j]:
                    with st.container(border=True):
                        st.subheader(item['상호'])
                        st.caption(f"주소: {item['지역']}")
                        
                        # [에러 수정 부분] 검색어 생성 및 구글 링크 연결
                        search_query = urllib.parse.quote(f"{item['지역']} {item['상호']} 평점")
                        final_url = f"https://www.google.com/search?q={search_query}"
                        
                        st.link_button("⭐ 평점/리뷰 보기", final_url, use_container_width=True)
else:
    st.error("데이터를 불러올 수 없습니다. 파일명(restaurants.csv)과 열 순서를 확인해주세요.")

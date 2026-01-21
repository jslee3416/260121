import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# 2. 데이터 로딩 및 전처리
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    if not os.path.exists(file_name):
        return pd.DataFrame()

    for enc in ['utf-8-sig', 'cp949', 'utf-8']:
        try:
            df = pd.read_csv(file_name, encoding=enc, on_bad_lines='skip')
            if df is not None:
                # [요청 반영] 2번째 열(index 1): 상호명 / 4번째 열(index 3): 주소/지역
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str),
                    '주소': df.iloc[:, 3].astype(str)
                })
                # 4번째 열(주소)의 첫 단어를 '구'로 인식하여 필터링에 사용
                res_df['구'] = res_df['주소'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "기타")
                return res_df.dropna(subset=['상호']).reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 화면 구성
st.title("🍴 서울 맛집 가이드")
st.write("2번째 열의 식당명과 4번째 열의 지역 정보를 기반으로 구성되었습니다.")

if not df.empty:
    # --- 행정구역(4번째 열 기반) 선택 버튼 ---
    gu_list = sorted(df['구'].unique())
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    st.markdown("### 📍 지역구 선택")
    gu_cols = st.columns(8) # 8열로 배치하여 공간 효율화
    for i, gu in enumerate(gu_list):
        with gu_cols[i % 8]:
            if st.button(gu, use_container_width=True, key=f"btn_{gu}"):
                st.session_state.selected_gu = gu

    st.divider()
    st.header(f"🔎 {st.session_state.selected_gu} 맛집 리스트")

    # --- 맛집 리스트 그리드 출력 (3열 바둑판식) ---
    filtered_df = df[df['구'] == st.session_state.selected_gu].reset_index(drop=True)
    
    # 한 줄에 3개씩 출력
    for i in range(0, len(filtered_df), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(filtered_df):
                item = filtered_df.iloc[i + j]
                with cols[j]:
                    # 개별 식당 카드
                    with st.container(border=True):
                        st.subheader(item['상호'])
                        st.caption(f"위치: {item['주소']}")
                        
                        # [요청 반영] 2번째 열(상호)을 이용한 구글맵 및 평점 연계
                        # 주소와 상호를 조합해 검색 정확도를 높임
                        search_term = f"{item['주소']} {item['상호']}"
                        encoded_search = urllib.parse.quote(search_term)
                        
                        # 구글 검색(평점/리뷰) 링크
                        google_search_url = f"https://www.google.com/search?q={encoded_search}+평점+리뷰"
                        # 구글 지도 바로가기 링크
                        google_maps_url = f"https://www.google.com/maps/search/{encoded_search}"
                        
                        # 버튼 배치
                        btn_cols = st.columns(2)
                        with btn_cols[0]:
                            st.link_button("⭐ 평점 보기", google_search_url, use_container_width=True)
                        with btn_cols[1]:
                            st.link_button("🗺️ 지도 보기", google_maps_url, use_container_width=True)
else:
    st.error("데이터를 불러올 수 없습니다. 'restaurants.csv' 파일이 main.py와 동일한 위치에 있는지 확인해 주세요.")

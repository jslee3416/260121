import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# 2. 데이터 로딩 및 최적화
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    if not os.path.exists(file_name):
        return pd.DataFrame()

    # 인코딩 순차 시도
    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(file_name, encoding=enc, on_bad_lines='skip')
            if df is not None:
                # 2번째 열: 상호명(index 1) / 4번째 열: 주소(index 3)
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str).str.strip(),
                    '주소': df.iloc[:, 3].astype(str).str.strip()
                })
                # 주소에서 첫 번째 단어(구) 추출
                res_df['구'] = res_df['주소'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "기타")
                # 상호명이 비어있지 않은 데이터만 필터링
                return res_df[res_df['상호'] != 'nan'].reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 타이틀
st.title("🍴 서울 맛집 추천 리스트")

if not df.empty:
    # --- 행정구역 선택 버튼 ---
    gu_list = sorted([g for g in df['구'].unique() if '구' in g or '시' in g]) # 유효한 지역구만 필터링
    
    if 'selected_gu' not in st.session_state:
        st.session_state.selected_gu = gu_list[0]

    # 구 버튼 레이아웃 (가로 8열)
    gu_cols = st.columns(8)
    for i, gu in enumerate(gu_list):
        with gu_cols[i % 8]:
            # 버튼 클릭 시 세션 상태 업데이트 및 화면 새로고침
            if st.button(gu, use_container_width=True, key=f"gu_btn_{gu}"):
                st.session_state.selected_gu = gu
                st.rerun() # 즉시 반영을 위해 추가

    st.divider()
    st.subheader(f"✨ {st.session_state.selected_gu} 추천 맛집 (TOP 20)")

    # --- 데이터 필터링 및 출력 ---
    # 선택된 구에 해당하는 데이터를 찾고 인덱스를 초기화하여 꼬임 방지
    display_df = df[df['구'] == st.session_state.selected_gu].reset_index(drop=True)
    
    # 요청하신 대로 최대 20개까지만 노출
    final_list = display_df.head(20)

    if not final_list.empty:
        # 3열 그리드로 출력
        for i in range(0, len(final_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(final_list):
                    item = final_list.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {item['상호']}")
                            st.caption(f"📍 {item['주소']}")
                            
                            # 검색 링크 (상호 + 주소 조합으로 정확도 향상)
                            query_str = urllib.parse.quote(f"{item['주소']} {item['상호']}")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                st.link_button("⭐ 평점/리뷰", f"https://www.google.com/search?q={query_str}+평점", use_container_width=True)
                            with c2:
                                st.link_button("🗺️ 지도", f"https://www.google.com/maps/search/{query_str}", use_container_width=True)
    else:
        st.warning(f"{st.session_state.selected_gu} 지역에 해당하는 맛집 데이터가 없습니다.")

else:
    st.error("데이터를 불러올 수 없습니다. 'restaurants.csv' 파일과 폴더 위치를 확인해주세요.")

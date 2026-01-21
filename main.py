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

    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
        try:
            df = pd.read_csv(file_name, encoding=enc, on_bad_lines='skip')
            if df is not None:
                # 2번째 열: 상호(index 1) / 4번째 열: 주소(index 3)
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str).str.strip(),
                    '주소': df.iloc[:, 3].astype(str).str.strip()
                })
                # 주소에서 '구' 단위 추출
                res_df['구'] = res_df['주소'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "기타")
                return res_df[res_df['상호'] != 'nan'].reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 타이틀
st.title("🍴 서울 맛집 추천 리스트")

if not df.empty:
    # --- 행정구역 선택 (LoV / Selectbox 방식) ---
    gu_list = sorted([g for g in df['구'].unique() if '구' in g or '시' in g])
    
    # 사이드바 혹은 메인 상단에 LoV 배치 (여기서는 상단에 배치합니다)
    selected_gu = st.selectbox(
        "원하시는 지역구를 선택하세요",
        gu_list,
        index=0,
        help="리스트에서 지역을 선택하면 맛집 목록이 자동으로 업데이트됩니다."
    )

    st.divider()
    st.subheader(f"✨ {selected_gu} 추천 맛집 (TOP 20)")

    # --- 데이터 필터링 및 출력 ---
    display_df = df[df['구'] == selected_gu].reset_index(drop=True)
    final_list = display_df.head(20)

    if not final_list.empty:
        # 3열 그리드 출력
        for i in range(0, len(final_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(final_list):
                    item = final_list.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {item['상호']}")
                            st.caption(f"📍 {item['주소']}")
                            
                            query_str = urllib.parse.quote(f"{item['주소']} {item['상호']}")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                st.link_button("⭐ 평점/리뷰", f"https://www.google.com/search?q={query_str}+평점", use_container_width=True)
                            with c2:
                                st.link_button("🗺️ 지도", f"https://www.google.com/maps/search/{query_str}", use_container_width=True)
    else:
        st.info(f"{selected_gu} 지역에 해당하는 데이터가 없습니다.")

else:
    st.error("데이터를 불러올 수 없습니다. 'restaurants.csv' 파일 구성을 확인해주세요.")

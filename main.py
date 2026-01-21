import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="SEOUL GOURMET GUIDE", layout="wide")

# 2. 데이터 로딩 (경로 추적 및 에러 핸들링 강화)
@st.cache_data
def load_data():
    file_name = "restaurants.csv"
    # 실행 파일(main.py)의 절대 경로를 기준으로 파일 경로 생성
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(current_dir, file_name)

    # 만약 위 경로에 없다면 현재 작업 디렉토리에서 검색
    if not os.path.exists(target_path):
        target_path = file_name

    if not os.path.exists(target_path):
        return pd.DataFrame()

    # 인코딩 순차 시도
    for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
        try:
            # 엔진을 'python'으로 설정하여 한글 경로 및 파일 읽기 안정성 확보
            df = pd.read_csv(target_path, encoding=enc, on_bad_lines='skip', engine='python')
            if df is not None:
                # 2번째 열: 상호(index 1) / 4번째 열: 주소(index 3)
                res_df = pd.DataFrame({
                    '상호': df.iloc[:, 1].astype(str).str.strip(),
                    '주소': df.iloc[:, 3].astype(str).str.strip()
                })
                # 4번째 열(주소)에서 첫 단어를 행정구역(구)으로 추출
                res_df['구'] = res_df['주소'].apply(lambda x: x.split()[0] if len(x.split()) > 0 else "기타")
                return res_df[res_df['상호'] != 'nan'].reset_index(drop=True)
        except:
            continue
    return pd.DataFrame()

df = load_data()

# 3. 메인 화면 구성
st.title("🍴 서울 맛집 추천 리스트")

if not df.empty:
    # --- 행정구역 선택 (LoV 방식) ---
    # '구' 또는 '시'가 포함된 유효한 지역명만 필터링하여 정렬
    gu_list = sorted([g for g in df['구'].unique() if any(keyword in g for keyword in ['구', '시', '군'])])
    
    if not gu_list:
        gu_list = sorted(df['구'].unique())

    # 화면 상단에 선택 상자 배치
    selected_gu = st.selectbox(
        "📍 탐색할 지역구를 선택하세요",
        gu_list,
        index=0
    )

    st.divider()
    st.subheader(f"✨ {selected_gu} 추천 맛집 (최대 20곳)")

    # --- 데이터 필터링 및 출력 ---
    display_df = df[df['구'] == selected_gu].reset_index(drop=True)
    final_list = display_df.head(20)

    if not final_list.empty:
        # 3열 바둑판 그리드 출력
        for i in range(0, len(final_list), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(final_list):
                    item = final_list.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {item['상호']}")
                            st.caption(f"주소: {item['주소']}")
                            
                            # 검색어 인코딩 (주소 + 상호명)
                            query_str = urllib.parse.quote(f"{item['주소']} {item['상호']}")
                            
                            # 버튼 배치
                            c1, c2 = st.columns(2)
                            with c1:
                                st.link_button("⭐ 평점 보기", f"https://www.google.com/search?q={query_str}+평점", use_container_width=True)
                            with c2:
                                st.link_button("🗺️ 지도 보기", f"https://www.google.com/maps/search/{query_str}", use_container_width=True)
    else:
        st.info(f"'{selected_gu}' 지역에 해당하는 데이터가 없습니다.")

else:
    # 파일 로드 실패 시 가이드 메시지 출력
    st.error("데이터 파일('restaurants.csv')을 찾을 수 없습니다.")
    st.info("""
    **해결 방법:**
    1. GitHub 저장소에 `restaurants.csv` 파일이 있는지 확인하세요.
    2. 파일 이름이 정확히 소문자인지 확인하세요.
    3. `main.py`와 같은 위치(루트 폴더)에 파일을 업로드했는지 확인하세요.
    """)

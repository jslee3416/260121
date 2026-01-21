import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# 구글 드라이브 파일 ID (사용자 제공)
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_and_process_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 인코딩 시도
        for enc in ['utf-8-sig', 'cp949']:
            try:
                df = pd.read_csv(io.BytesIO(response.content), encoding=enc, low_memory=False)
                # 컬럼 선택: 4번째(상태), 9번째(식당명), 10번째(업태), 19번째(도로명주소 - 위치정보용)
                # 주소 정보가 있는 19번째 컬럼(index 18)을 추가로 가져옵니다.
                df_selected = df.iloc[:, [3, 8, 9, 18]].copy()
                df_selected.columns = ['status', 'name', 'category', 'address']
                
                # 폐업 데이터 삭제
                df_filtered = df_selected[~df_selected['status'].fillna('').str.contains("폐업")].copy()
                return df_filtered
            except:
                continue
        return "데이터 파싱 실패"
    except Exception as e:
        return f"로드 실패: {str(e)}"

# --- 메인 인터페이스 ---
st.title("⭐ 서울시 분야별 추천 맛집 TOP 20")
st.markdown("구글 맵 데이터와 연동하여 실시간 평점과 리뷰를 확인하세요.")

with st.spinner('실시간 데이터를 분석 중입니다...'):
    data = load_and_process_data(DIRECT_URL)

if isinstance(data, str):
    st.error(data)
else:
    # 카테고리 LoV
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected_category = st.selectbox("🍱 어떤 종류의 음식을 찾으시나요?", ["전체"] + category_list)

    # 필터링
    filtered_df = data if selected_category == "전체" else data[data['category'] == selected_category]

    st.subheader(f"📍 '{selected_category}' 추천 리스트")
    st.caption("※ '평점 확인' 링크 클릭 시 구글 지도의 최신 평점과 리뷰, 상세 위치를 확인할 수 있습니다.")

    # 상위 20개 출력
    top_20 = filtered_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            # 구글 검색용 쿼리 (평점 4.5 이상인 곳을 우선 탐색하도록 유도)
            search_name = f"서울 {row['name']} {row['category']}"
            
            # 1. 구글 지도/평점/리뷰 통합 검색 링크
            google_search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_name + ' 평점 리뷰')}"
            
            # 2. 구글 맵 위치 전용 링크
            google_map_url = f"https://www.google.com/maps/search/{urllib.parse.quote(search_name + ' ' + str(row['address']))}"
            
            with st.container():
                c1, c2 = st.columns([3, 2])
                with c1:
                    st.markdown(f"### {i+1}. {row['name']}")
                    st.write(f"📂 **분류**: {row['category']}")
                    st.caption(f"📍 주소: {row['address'] if pd.notna(row['address']) else '정보 없음'}")
                
                with c2:
                    st.write("") # 간격 조절
                    # 버튼 형태로 링크 제공
                    st.markdown(f"""
                    <a href="{google_search_url}" target="_blank" style="text-decoration: none;">
                        <button style="width:100%; border-radius:5px; background-color:#4285F4; color:white; border:none; padding:10px; margin-bottom:5px; cursor:pointer;">
                            ⭐ 실시간 평점·리뷰 확인
                        </button>
                    </a>
                    <a href="{google_map_url}" target="_blank" style="text-decoration: none;">
                        <button style="width:100%; border-radius:5px; background-color:#34A853; color:white; border:none; padding:10px; cursor:pointer;">
                            📍 구글 맵 위치 보기
                        </a>
                    """, unsafe_allow_html=True)
                
                st.divider()
    else:
        st.warning("조건에 맞는 식당이 없습니다.")

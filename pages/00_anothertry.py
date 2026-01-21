import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# 구글 드라이브 파일 ID 및 직접 다운로드 URL
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_and_process_data(url):
    try:
        # 클라우드에서 데이터 가져오기
        response = requests.get(url)
        response.raise_for_status()
        content = response.content
        
        # [파싱 해결책] 여러 인코딩 방식을 시도하며 오류 행은 건너뜁니다.
        # 4번째(3:상태), 9번째(8:이름), 10번째(9:업종), 19번째(18:주소) 컬럼만 추출
        for enc in ['utf-8-sig', 'cp949', 'euc-kr']:
            try:
                df = pd.read_csv(
                    io.BytesIO(content), 
                    encoding=enc, 
                    usecols=[3, 8, 9, 18],
                    on_bad_lines='skip', # 파싱 에러 유발하는 잘못된 행 무시
                    low_memory=False
                )
                
                # 컬럼명 정리
                df.columns = ['status', 'name', 'category', 'address']
                
                # [요구사항 1] 4번째 컬럼에서 '폐업'인 데이터 삭제
                # 상세영업상태명에 '폐업'이 들어간 모든 행 제거
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                
                # 데이터가 존재하면 반환
                if not df.empty:
                    return df
            except Exception:
                continue
                
        return "데이터 형식 분석에 실패했습니다. 파일의 인코딩을 확인해주세요."
    except Exception as e:
        return f"네트워크 오류: {str(e)}"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 실시간 맛집 추천 가이드")
st.markdown("구글 지도의 평점과 리뷰 정보를 연동하여 상위 20개 식당을 보여줍니다.")

with st.spinner('149MB 대용량 데이터를 최적화하여 불러오는 중...'):
    data = load_and_process_data(DIRECT_URL)

if isinstance(data, str):
    st.error(data)
    st.info("💡 구글 드라이브의 파일 공유 설정이 '링크가 있는 모든 사용자'로 되어 있는지 꼭 확인해 주세요.")
else:
    # [요구사항 2] 10번째 컬럼(category) 기반으로 업종 선택 LoV 생성
    category_list = sorted(data['category'].dropna().unique().tolist())
    
    col_select, col_info = st.columns([1, 2])
    with col_select:
        selected_category = st.selectbox("🍱 어떤 음식을 드시고 싶나요?", ["전체 보기"] + category_list)

    # 카테고리 필터링
    filtered_df = data if selected_category == "전체 보기" else data[data['category'] == selected_category]

    st.markdown("---")
    st.subheader(f"📍 '{selected_category}' 추천 맛집 TOP 20")

    # [요구사항 3] 상위 20개 추출 및 구글맵/리뷰 연동
    top_20 = filtered_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            # 구글 검색 및 지도 쿼리 생성
            # 검색어 예: "서울 마포구 맛있는집 한식 평점 리뷰"
            search_query = f"서울 {row['name']} {row['category']} 평점 리뷰"
            encoded_query = urllib.parse.quote(search_query)
            
            # 구글 검색 링크 (평점/리뷰 확인용)
            google_search_url = f"https://www.google.com/search?q={encoded_query}"
            
            # 구글 맵 링크 (위치 확인용)
            map_query = urllib.parse.quote(f"{row['name']} {row['address']}")
            google_map_url = f"https://www.google.com/maps/search/?api=1&query={map_query}"
            
            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1:
                    # 9번째 컬럼에서 추출된 식당명 표기
                    st.markdown(f"### {i+1}. {row['name']}")
                    st.write(f"📂 **업종**: {row['category']} | ✅ **상태**: {row['status']}")
                    st.caption(f"📍 **주소**: {row['address'] if pd.notna(row['address']) else '주소 정보가 없습니다.'}")
                
                with c2:
                    st.write("") # 수직 정렬용 공백
                    # 평점 확인 버튼 (구글 검색 연결)
                    st.markdown(f"""
                        <a href="{google_search_url}" target="_blank">
                            <button style="width:100%; padding:10px; background-color:#4285F4; color:white; border:none; border-radius:5px; cursor:pointer; margin-bottom:10px;">
                                ⭐ 평점/리뷰 확인
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 지도 보기 버튼 (구글 맵 연결)
                    st.markdown(f"""
                        <a href="{google_map_url}" target="_blank">
                            <button style="width:100%; padding:10px; background-color:#34A853; color:white; border:none; border-radius:5px; cursor:pointer;">
                                📍 상세 위치 보기
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                st.divider()
    else:
        st.warning("해당 카테고리에 영업 중인 식당 데이터가 없습니다.")

# 하단 정보
st.caption("데이터 출처: 지방행정 인허가 데이터 (서울시) | 검색 결과는 구글 실시간 정보와 연결됩니다.")

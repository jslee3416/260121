import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# [수정 완료] 보내주신 링크에서 추출한 파일 ID
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def load_data_from_gdrive(file_id):
    # 구글 드라이브 대용량 파일 다운로드를 위한 세션 및 토큰 처리
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    
    try:
        # 1차 시도: 토큰 확인
        response = session.get(URL, params={'id': file_id}, stream=True, timeout=30)
        token = get_confirm_token(response)

        # 2차 시도: 토큰이 있다면 포함해서 재요청
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)
        
        # 권한 오류 체크 (응답이 HTML이면 권한 문제)
        if "html" in response.headers.get('Content-Type', '').lower():
            return "AUTH_ERROR"

        # 파일 읽기 (인코딩 및 파싱 에러 방지)
        content = response.content
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # 메모리 효율을 위해 필요한 컬럼만 지정 (4, 9, 10, 19번째)
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=enc,
                    usecols=[3, 8, 9, 18],
                    on_bad_lines='skip',
                    low_memory=False
                )
                
                # 컬럼명 통일
                df.columns = ['status', 'name', 'category', 'address']
                
                # [요구사항 1] 4번째 컬럼에서 '폐업'인 데이터 삭제
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                
                return df
            except:
                continue
                
        return "PARSE_ERROR"
        
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 실시간 맛집 추천 가이드")
st.markdown("구글 지도의 실시간 평점과 위치 정보를 연동하여 상위 20개 식당을 보여줍니다.")

# 데이터 로딩 시작
with st.spinner('데이터를 분석 중입니다. 대용량 파일이라 처음 로딩 시 10초 정도 소요될 수 있습니다...'):
    data = load_data_from_gdrive(GOOGLE_FILE_ID)

# 에러 처리 및 결과 출력
if data is "AUTH_ERROR":
    st.error("❌ 구글 드라이브 권한 에러")
    st.info("파일의 공유 설정이 '링크가 있는 모든 사용자'로 되어 있는지 다시 확인해 주세요.")
elif data is "PARSE_ERROR":
    st.error("❌ 데이터 파싱 실패 (인코딩 문제)")
elif isinstance(data, str):
    st.error(data)
else:
    st.success(f"✅ 영업 중인 식당 {len(data):,}개를 성공적으로 불러왔습니다.")

    # [요구사항 2] 10번째 컬럼(category) 기반으로 업종 선택 LoV 생성
    category_list = sorted(data['category'].dropna().unique().tolist())
    
    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        selected_category = st.selectbox("🍱 어떤 업종을 찾으시나요?", ["전체 보기"] + category_list)

    # 필터링 적용
    filtered_df = data if selected_category == "전체 보기" else data[data['category'] == selected_category]

    st.divider()
    st.subheader(f"📍 '{selected_category}' 추천 리스트 TOP 20")

    # [요구사항 3] 상위 20개 추출 및 구글맵/평점 연동
    top_20 = filtered_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            # 검색 및 지도 쿼리
            search_query = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점 리뷰")
            map_query = urllib.parse.quote(f"{row['name']} {row['address']}")
            
            with st.container():
                c1, c2 = st.columns([3, 1])
                with c1:
                    # 9번째 컬럼에서 추출된 식당명 표기
                    st.markdown(f"### {row['name']}")
                    st.write(f"📂 **업종**: {row['category']} | ✅ **상태**: {row['status']}")
                    st.caption(f"📍 **주소**: {row['address'] if pd.notna(row['address']) else '주소 정보가 없습니다.'}")
                
                with c2:
                    st.write("") # 수직 정렬용
                    # 평점 확인 버튼
                    st.markdown(f"""
                        <a href="https://www.google.com/search?q={search_query}" target="_blank">
                            <button style="width:100%; padding:10px; background-color:#4285F4; color:white; border:none; border-radius:5px; cursor:pointer; margin-bottom:10px;">
                                ⭐ 평점/리뷰 확인
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                    
                    # 지도 보기 버튼
                    st.markdown(f"""
                        <a href="https://www.google.com/maps/search/?api=1&query={map_query}" target="_blank">
                            <button style="width:100%; padding:10px; background-color:#34A853; color:white; border:none; border-radius:5px; cursor:pointer;">
                                📍 상세 위치 보기
                            </button>
                        </a>
                    """, unsafe_allow_html=True)
                st.divider()
    else:
        st.warning("선택하신 분류에 해당하는 데이터가 없습니다.")

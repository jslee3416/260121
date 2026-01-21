import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# 보내주신 파일 ID
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def download_large_file_from_gdrive(file_id):
    """구글 드라이브의 대용량 파일 보안 경고(100MB+)를 우회하는 함수"""
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    
    # 1차 요청: 보안 토큰(confirm)이 필요한지 확인
    response = session.get(URL, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    # 2차 요청: 토큰이 있다면 토큰을 실어서 실제 데이터 요청
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)
    
    # 응답이 HTML(권한 안내 페이지)인지 최종 확인
    if "html" in response.headers.get('Content-Type', '').lower():
        return None
        
    return response.content

@st.cache_data(show_spinner=False)
def process_restaurant_data(content):
    """다운로드된 바이너리 데이터를 분석하고 요구사항에 맞게 정제"""
    if content is None:
        return "AUTH_ERROR"
        
    # 인코딩 순차 시도
    for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
        try:
            # 4번째(3:상태), 9번째(8:명칭), 10번째(9:업종), 19번째(18:주소) 추출
            df = pd.read_csv(
                io.BytesIO(content),
                encoding=enc,
                usecols=[3, 8, 9, 18],
                on_bad_lines='skip',
                low_memory=False,
                dtype=str
            )
            df.columns = ['status', 'name', 'category', 'address']
            
            # [요구사항] '폐업'인 데이터 삭제
            df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
            return df
        except:
            continue
    return "PARSE_ERROR"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 실시간 맛집 가이드 (TOP 20)")
st.info("구글 클라우드에서 대용량 데이터를 동기화 중입니다. 잠시만 기다려 주세요.")

# 실행 로직
raw_data = download_large_file_from_gdrive(GOOGLE_FILE_ID)
data = process_restaurant_data(raw_data)

if data == "AUTH_ERROR":
    st.error("❌ AUTH_ERROR: 구글 드라이브가 여전히 접근을 거부합니다.")
    st.markdown("""
    **확인사항:**
    1. 구글 드라이브에서 파일 우클릭 -> **공유** -> 일반 액세스가 **'링크가 있는 모든 사용자'**로 되어 있는지 꼭 확인해주세요.
    2. 설정을 바꿨다면, 이 앱 화면에서 키보드의 **'R'** 키를 눌러 새로고침 하세요.
    """)
elif data == "PARSE_ERROR":
    st.error("❌ 데이터 인코딩 형식(UTF-8/CP949)이 맞지 않아 읽기에 실패했습니다.")
elif isinstance(data, pd.DataFrame):
    st.success(f"✅ {len(data):,}개의 영업 중인 식당 데이터를 불러왔습니다.")

    # [요구사항] 10번째 컬럼 기반 업종 선택 LoV
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered = data if selected == "전체" else data[data['category'] == selected]

    st.divider()
    st.subheader(f"📍 '{selected}' 검색 결과 (최상위 20개)")

    # 상위 20개 식당 출력
    for i, row in filtered.head(20).iterrows():
        # 검색/위치 쿼리 생성
        search_q = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점 리뷰")
        map_q = urllib.parse.quote(f"{row['name']} {row['address']}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['name']}")
            st.write(f"📂 **업종**: {row['category']} | 📍 **주소**: {row['address']}")
        with col2:
            st.write("") # 간격 조절
            st.markdown(f"[⭐ 평점확인](https://www.google.com/search?q={search_q})")
            st.markdown(f"[📍 지도보기](https://www.google.com/maps/search/?api=1&query={map_q})")
        st.divider()

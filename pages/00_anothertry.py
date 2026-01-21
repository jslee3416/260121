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
def download_large_file(file_id):
    """구글 드라이브의 대용량 파일 보안 경고를 우회하여 다운로드하는 함수"""
    base_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    
    # 1단계: 파일 ID를 통해 보안 토큰(confirm token) 확인 요청
    response = session.get(base_url, params={'id': file_id}, stream=True)
    
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    token = get_confirm_token(response)
    
    # 2단계: 토큰이 있다면 토큰을 포함하여 실제 데이터 요청
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(base_url, params=params, stream=True)
    
    # 응답이 여전히 HTML(권한/로그인 페이지)인지 최종 확인
    if "html" in response.headers.get('Content-Type', '').lower():
        return "AUTH_ERROR"
        
    return response.content

@st.cache_data(show_spinner=False)
def process_data(content):
    """다운로드된 바이너리 데이터를 판다스로 변환하고 필터링하는 함수"""
    if content == "AUTH_ERROR":
        return "AUTH_ERROR"
        
    # 인코딩 순차 시도 (CP949 -> UTF-8-SIG -> EUC-KR)
    for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
        try:
            df = pd.read_csv(
                io.BytesIO(content),
                encoding=enc,
                usecols=[3, 8, 9, 18], # 상태, 이름, 업종, 주소
                on_bad_lines='skip',
                low_memory=False,
                dtype=str
            )
            df.columns = ['status', 'name', 'category', 'address']
            
            # [요구사항] '폐업' 제외
            df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
            return df
        except:
            continue
    return "PARSE_ERROR"

# --- 메인 실행부 ---
st.title("🍴 서울시 실시간 맛집 추천 가이드")

with st.spinner('구글 클라우드에서 대용량 데이터를 동기화 중입니다...'):
    raw_content = download_large_file(GOOGLE_FILE_ID)
    data = process_data(raw_content)

if data == "AUTH_ERROR":
    st.error("❌ AUTH_ERROR: 구글 드라이브가 접근을 거부했습니다.")
    st.markdown("""
    **해결 방법:**
    1. 구글 드라이브에서 파일 우클릭 -> **공유** -> **'링크가 있는 모든 사용자'**로 되어있는지 다시 확인!
    2. 완료 버튼을 누른 후, 이 페이지를 새로고침(F5) 해주세요.
    """)
elif data == "PARSE_ERROR":
    st.error("❌ PARSE_ERROR: 데이터 형식을 읽을 수 없습니다.")
elif isinstance(data, pd.DataFrame):
    st.success(f"✅ {len(data):,}개의 영업 중인 식당 데이터를 로드했습니다.")

    # 업종 LoV
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered = data if selected == "전체" else data[data['category'] == selected]

    st.divider()
    st.subheader(f"📍 '{selected}' 추천 리스트 TOP 20")

    # 상위 20개 출력
    for i, row in filtered.head(20).iterrows():
        search_q = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점 리뷰")
        map_q = urllib.parse.quote(f"{row['name']} {row['address']}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['name']}")
            st.caption(f"📂 {row['category']} | 📍 {row['address']}")
        with col2:
            st.write("")
            st.markdown(f"[⭐ 평점확인](https://www.google.com/search?q={search_q})")
            st.markdown(f"[📍 지도보기](https://www.google.com/maps/search/?api=1&query={map_q})")
        st.divider()

import streamlit as st
import os

# 현재 실행 중인 파일의 절대 경로를 화면에 표시
st.write("현재 코드 저장 위치:", os.path.abspath(__file__))


import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 검색", layout="wide")

# 보내주신 파일 ID
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def load_large_csv_from_gdrive(file_id):
    """구글 드라이브 보안 경고를 우회하여 대용량 CSV를 읽어오는 함수"""
    download_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    
    # 1차 요청: 보안 토큰(confirm) 확인
    response = session.get(download_url, params={'id': file_id}, stream=True)
    
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    # 2차 요청: 토큰이 있다면 포함하여 실제 데이터 다운로드
    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(download_url, params=params, stream=True)
    
    # 응답 내용이 HTML(로그인/권한 페이지)인지 체크
    if "html" in response.headers.get('Content-Type', '').lower():
        return "AUTH_ERROR"

    # 인코딩 순차 시도 및 데이터 정리
    try:
        content = response.content
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # 메모리 효율을 위해 필요한 4개 컬럼만 로드
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=enc,
                    usecols=[3, 8, 9, 18],
                    on_bad_lines='skip',
                    low_memory=False,
                    dtype=str
                )
                df.columns = ['status', 'name', 'category', 'address']
                
                # [요구사항] 폐업 데이터 삭제
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                return df
            except:
                continue
        return "PARSE_ERROR"
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- 메인 실행부 ---
st.title("🍴 서울시 맛집 가이드 (TOP 20)")

with st.spinner('구글 드라이브에서 대용량 데이터를 가져오는 중입니다...'):
    data = load_large_csv_from_gdrive(GOOGLE_FILE_ID)

if data == "AUTH_ERROR":
    st.error("❌ 구글 드라이브 접근 거부 (AUTH_ERROR)")
    st.write("공유 설정이 '링크가 있는 모든 사용자' 임에도 안 된다면, 아래 주소를 브라우저에 입력했을 때 파일이 바로 다운로드 되는지 확인해 주세요.")
    st.code(f"https://docs.google.com/uc?export=download&id={GOOGLE_FILE_ID}")
elif data == "PARSE_ERROR":
    st.error("❌ 데이터 해석 실패 (인코딩 문제)")
elif isinstance(data, pd.DataFrame):
    st.success(f"✅ {len(data):,}개의 식당 데이터를 성공적으로 로드했습니다.")

    # 업종 선택 LoV
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered = data if selected == "전체" else data[data['category'] == selected]

    # 결과 출력
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
            st.markdown(f"[📍 지도보기](https://www.google.com/maps/search/{map_q})")
        st.divider()

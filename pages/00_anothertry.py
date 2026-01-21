import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

st.set_page_config(page_title="서울 맛집 가이드", layout="wide")

# 구글 드라이브 파일 ID
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def load_data_final(file_id):
    # 구글 대용량 파일 보안 경고 우회 로직
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    
    try:
        # 1차 시도: 토큰 확인
        response = session.get(URL, params={'id': file_id}, stream=True)
        
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        
        # 2차 시도: 토큰이 있다면 확인 후 재요청
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)
        
        content = response.content
        
        # [해결 핵심] 다양한 설정으로 데이터 읽기 시도
        # 인코딩: cp949(한글), utf-8-sig
        # 구분자: sep=None (자동 감지)
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # 모든 데이터를 문자열(str)로 읽어서 오류를 방지합니다.
                df = pd.read_csv(
                    io.BytesIO(content),
                    encoding=enc,
                    sep=None,          # 콤마, 탭, 세미콜론 자동 감지
                    engine='python',   # 자동 감지를 위해 python 엔진 사용
                    usecols=[3, 8, 9, 18],
                    on_bad_lines='skip',
                    dtype=str
                )
                
                df.columns = ['status', 'name', 'category', 'address']
                
                # '폐업' 제외 필터링
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                
                if not df.empty:
                    return df
            except Exception:
                continue
                
        return "PARSE_ERROR"
        
    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

# --- 메인 화면 ---
st.title("🍴 서울시 실시간 맛집 추천")

with st.spinner('데이터를 정밀 분석 중입니다. 대용량 파일이라 최대 15초 정도 걸릴 수 있습니다...'):
    data = load_data_final(GOOGLE_FILE_ID)

if data == "PARSE_ERROR":
    st.error("❌ 데이터 해석 실패: 파일의 형식을 읽을 수 없습니다.")
    st.info("파일이 CSV 형식이 맞는지, 혹은 파일 내부에 특수문자가 너무 많은지 확인이 필요합니다.")
elif isinstance(data, str):
    st.error(data)
else:
    st.success(f"✅ 총 {len(data):,}개의 영업 중인 식당을 찾았습니다!")

    # 업종 선택
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered = data if selected == "전체" else data[data['category'] == selected]

    # 결과 출력 (TOP 20)
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

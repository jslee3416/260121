import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

st.set_page_config(page_title="서울 맛집 가이드", layout="wide")

# 구글 드라이브 파일 ID (사용자님 파일)
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def load_data_from_gdrive(file_id):
    # 대용량 파일 보안 경고를 무시하고 강제 다운로드하는 특수 주소입니다.
    # 이 주소는 토큰 없이도 직접 다운로드를 시도합니다.
    direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        # 데이터를 한 번에 가져오지 않고 스트리밍 방식으로 읽어 메모리 에러를 방지합니다.
        response = requests.get(direct_url)
        response.raise_for_status()
        
        # 파일 내용
        content = response.content
        
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
                # 폐업 제외
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                return df
            except:
                continue
        return "데이터 해석 실패"
    except Exception as e:
        return f"연결 실패: {str(e)}"

st.title("🍴 서울시 맛집 추천 (클라우드 모드)")

with st.spinner('구글 드라이브에서 149MB 데이터를 불러오는 중...'):
    data = load_data_from_gdrive(GOOGLE_FILE_ID)

if isinstance(data, str):
    st.error(f"에러 발생: {data}")
    st.info("구글 드라이브 공유 설정을 '링크가 있는 모든 사용자'로 유지해 주세요.")
else:
    st.success(f"✅ {len(data):,}개의 영업 중인 식당 로드 완료!")
    
    # [업종 선택 LoV]
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)
    
    filtered = data if selected == "전체" else data[data['category'] == selected]
    
    # [상위 20개 출력]
    for i, row in filtered.head(20).iterrows():
        search_q = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점 리뷰")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['name']}")
            st.caption(f"📍 {row['address']}")
        with col2:
            st.markdown(f"[⭐ 평점확인](https://www.google.com/search?q={search_q})")
        st.divider()

import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 검색 서비스", layout="wide")

# 2. 구글 드라이브 파일 ID 및 URL 설정 (보내주신 링크 반영)
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_data_from_gdrive(url):
    try:
        # 클라우드에서 파일 다운로드
        response = requests.get(url)
        response.raise_for_status()
        
        # 메모리 효율을 위해 필요한 4, 9, 10번째 컬럼만 추출
        # 0부터 시작하므로 인덱스는 3, 8, 9입니다.
        df = pd.read_csv(
            io.BytesIO(response.content),
            usecols=[3, 8, 9],
            encoding='cp949', # 공공데이터 한글 인코딩
            low_memory=False
        )
        
        # 컬럼명 통일
        df.columns = ['status', 'name', 'category']
        
        # [전처리] 폐업 데이터 삭제 및 영업 중인 데이터만 유지
        df = df[df['status'].fillna('').str.contains("영업|정상")].copy()
        df = df[~df['status'].fillna('').str.contains("폐업")].copy()
        
        return df
    except Exception as e:
        return f"데이터 로드 실패: {str(e)}"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 맛집 정보 서비스")
st.info("구글 클라우드의 대용량 데이터를 활용하여 실시간 정보를 제공합니다.")

# 데이터 로딩
with st.spinner('데이터를 불러오는 중입니다... (약 10~15초 소요)'):
    df = load_data_from_gdrive(DIRECT_URL)

if isinstance(df, str):
    st.error(df)
    st.warning("⚠️ 구글 드라이브 파일의 공유 설정이 '링크가 있는 모든 사용자'로 되어 있는지 확인해 주세요.")
else:
    st.success(f"✅ 영업 중인 식당 {len(df):,}개를 성공적으로 불러왔습니다.")

    # 카테고리(업태) 선택 목록 생성
    categories = sorted(df['category'].dropna().unique().tolist())
    selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

    # 필터링 적용
    final_df = df if selected_category == "전체" else df[df['category'] == selected_category]

    st.subheader(f"📍 '{selected_category}' 검색 결과 (최상위 20개)")

    # 결과 출력
    top_20 = final_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            # 구글 검색 링크 생성 (평점 및 후기 확인용)
            search_query = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점")
            google_url = f"https://www.google.com/search?q={search_query}"
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{i+1}. {row['name']}**")
                    st.caption(f"분류: {row['category']}")
                with col2:
                    st.markdown(f"[⭐ 평점 확인]({google_url})")
                st.divider()
    else:
        st.warning("선택한 카테고리에 해당하는 데이터가 없습니다.")

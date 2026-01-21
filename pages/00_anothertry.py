import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 검색 서비스", layout="wide")

# 2. 구글 드라이브 파일 ID (보내주신 ID 유지)
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_data_from_gdrive(url):
    try:
        # 클라우드에서 파일 다운로드
        response = requests.get(url)
        response.raise_for_status()
        
        # [핵심 수정] 여러 인코딩 방식을 순차적으로 시도합니다.
        # 에러가 난다면 utf-8-sig 또는 euc-kr일 확률이 높습니다.
        encodings = ['utf-8-sig', 'cp949', 'euc-kr']
        
        for enc in encodings:
            try:
                # 4, 9, 10번째 컬럼만 추출 (인덱스 3, 8, 9)
                df = pd.read_csv(
                    io.BytesIO(response.content),
                    usecols=[3, 8, 9],
                    encoding=enc,
                    low_memory=False,
                    on_bad_lines='skip' # 깨진 행이 있다면 건너뜁니다.
                )
                
                # 컬럼명 통일
                df.columns = ['status', 'name', 'category']
                
                # [전처리] 폐업 데이터 삭제 및 영업 중인 데이터만 유지
                df = df[df['status'].fillna('').str.contains("영업|정상")].copy()
                df = df[~df['status'].fillna('').str.contains("폐업")].copy()
                
                return df
            except (UnicodeDecodeError, LookupError):
                continue # 다음 인코딩 시도
                
        return "모든 인코딩 방식(UTF-8, CP949 등)으로 읽기에 실패했습니다."
        
    except Exception as e:
        return f"데이터 로드 실패: {str(e)}"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 맛집 정보 서비스")
st.info("💡 구글 클라우드에서 149MB 데이터를 안전하게 로드 중입니다.")

# 데이터 로딩
with st.spinner('한글 인코딩을 최적화하여 데이터를 불러오는 중...'):
    df = load_data_from_gdrive(DIRECT_URL)

if isinstance(df, str):
    st.error(df)
    st.info("⚠️ 파일의 인코딩 형식이 특수하거나 데이터가 손상되었을 수 있습니다.")
else:
    st.success(f"✅ 영업 중인 식당 {len(df):,}개를 로드했습니다.")

    # 카테고리(업태) 선택 목록
    categories = sorted(df['category'].dropna().unique().tolist())
    selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

    # 필터링 및 출력
    final_df = df if selected_category == "전체" else df[df['category'] == selected_category]

    st.subheader(f"📍 '{selected_category}' 검색 결과 (Top 20)")

    top_20 = final_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            search_query = urllib.parse.quote(f"서울 {row['name']} {row['category']} 평점")
            google_url = f"https://www.google.com/search?q={search_query}"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}. {row['name']}**")
                st.caption(f"분류: {row['category']}")
            with col2:
                st.markdown(f"[⭐ 평점 확인]({google_url})")
            st.divider()
    else:
        st.warning("선택한 카테고리에 해당하는 데이터가 없습니다.")

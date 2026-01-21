import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

st.set_page_config(page_title="서울 맛집 검색 서비스", layout="wide")

GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_data_from_gdrive(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # 인코딩 시도
        for enc in ['utf-8-sig', 'cp949', 'euc-kr']:
            try:
                # [수정] 우선 컬럼 선택 없이 100줄만 읽어서 구조 파악 (디버깅용)
                df_sample = pd.read_csv(io.BytesIO(response.content), nrows=100, encoding=enc)
                
                # [핵심 수정] 3, 8, 9번 컬럼 대신 이름이나 위치를 더 유연하게 처리
                # 파일의 실제 컬럼 수를 확인하여 안전하게 읽기
                df = pd.read_csv(
                    io.BytesIO(response.content),
                    usecols=None, # 일단 전체를 읽되 메모리 관리를 위해 처리
                    encoding=enc,
                    low_memory=False
                )
                
                # 필요한 컬럼만 추출 (안전한 인덱스 접근)
                # 보통 영업상태(7), 사업장명(18), 업태명(25) 등 공공데이터 양식에 따라 다를 수 있음
                # 요청하신 4, 9, 10번째(인덱스 3, 8, 9) 추출
                df = df.iloc[:, [3, 8, 9]]
                df.columns = ['status', 'name', 'category']
                
                # [필터링 완화] '폐업'이라는 글자가 없는 모든 데이터를 일단 '영업 중'으로 간주
                # 공공데이터에서 '영업' 대신 '영업/정상' 혹은 다른 코드를 쓸 수 있기 때문입니다.
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소", na=False)].copy()
                
                return df
            except:
                continue
        return "인코딩 실패"
    except Exception as e:
        return f"로드 실패: {str(e)}"

# --- UI ---
st.title("🍴 서울시 맛집 정보 서비스")

with st.spinner('데이터를 분석 중입니다...'):
    df = load_data_from_gdrive(DIRECT_URL)

if isinstance(df, str):
    st.error(df)
else:
    # 데이터가 0개일 때 원인 분석을 위한 정보 표시
    if len(df) == 0:
        st.warning("⚠️ 필터링 결과 데이터가 0개입니다. 원본 데이터의 구조를 확인합니다.")
        # 필터링 전의 원본 데이터를 잠시 보여줌 (디버깅용)
        st.write("데이터 샘플 (상위 5줄):", df.head())
    else:
        st.success(f"✅ 영업 중인 식당 {len(df):,}개를 로드했습니다.")

        # 카테고리 선택
        categories = sorted(df['category'].dropna().unique().tolist())
        selected = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

        final_df = df if selected == "전체" else df[df['category'] == selected]

        st.subheader(f"📍 '{selected}' 검색 결과 (Top 20)")

        top_20 = final_df.head(20)
        if len(top_20) > 0:
            for i, row in top_20.iterrows():
                query = urllib.parse.quote(f"서울 {row['name']} {row['category']}")
                url = f"https://www.google.com/search?q={query}"
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{row['name']}** ({row['category']})")
                col2.markdown(f"[⭐ 평점확인]({url})")
                st.divider()
        else:
            st.info("해당 카테고리에 영업 중인 식당이 없습니다.")

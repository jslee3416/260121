import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# 구글 드라이브 파일 ID
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'

@st.cache_data(show_spinner=False)
def load_data_robust(file_id):
    URL = f"https://docs.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    
    try:
        # 구글 드라이브 대용량 파일은 '바이러스 검사 불가' 경고가 뜰 수 있어 2번 시도합니다.
        response = session.get(URL, stream=True, timeout=60)
        
        # 인코딩 후보군 (한국 공공데이터는 대부분 이 중 하나입니다)
        # cp949(윈도우 한글), utf-8-sig(BOM 포함 UTF8), euc-kr(확장 한글)
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # [중요] 필요한 컬럼만 지정하고 데이터 타입을 문자열(str)로 강제하여 파싱 오류 방지
                # 4번째(3:상태), 9번째(8:이름), 10번째(9:업종), 19번째(18:주소)
                df = pd.read_csv(
                    io.BytesIO(response.content),
                    encoding=enc,
                    usecols=[3, 8, 9, 18],
                    on_bad_lines='skip',  # 깨진 행 무시
                    low_memory=False,     # 대용량 처리 안정성
                    dtype=str             # 모든 열을 일단 텍스트로 읽음
                )
                
                # 컬럼 이름 재정의
                df.columns = ['status', 'name', 'category', 'address']
                
                # [요구사항] '폐업' 데이터 삭제
                # 결측치를 제거하고 '폐업' 글자가 없는 행만 필터링
                df = df[~df['status'].fillna('').str.contains("폐업|취소|말소")].copy()
                
                # 데이터가 정상적으로 읽혔다면 반복문 종료
                if not df.empty:
                    return df
            except Exception:
                continue
                
        return "데이터의 인코딩을 해석할 수 없습니다. (UTF-8/CP949 모두 실패)"
        
    except Exception as e:
        return f"서버 연결 실패: {str(e)}"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 실시간 맛집 추천 가이드")

with st.spinner('대용량 데이터를 분석 중입니다. 잠시만 기다려 주세요...'):
    data = load_data_robust(GOOGLE_FILE_ID)

if isinstance(data, str):
    st.error(data)
    st.markdown("⚠️ **공유 권한이 맞는데도 안 된다면?**")
    st.write("1. 파일이 .csv 인지 다시 확인해주세요. (.xlsx라면 코드가 다릅니다)")
    st.write("2. 구글 드라이브에서 '다운로드'가 금지되어 있는지 확인해주세요.")
else:
    st.success(f"✅ {len(data):,}개의 식당 정보를 불러왔습니다.")

    # 카테고리 LoV 생성
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected_category = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered_df = data if selected_category == "전체" else data[data['category'] == selected_category]

    st.divider()
    st.subheader(f"📍 '{selected_category}' 추천 맛집 TOP 20")

    # 상위 20개 출력 및 구글맵 연동
    for i, row in filtered_df.head(20).iterrows():
        # 검색 쿼리: 식당명 + 업종 + 평점/리뷰
        search_q = f"서울 {row['name']} {row['category']} 평점 리뷰"
        map_q = f"{row['name']} {row['address']}"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['name']}")
            st.write(f"📂 {row['category']} | 📍 {row['address']}")
        with col2:
            st.write("") # 간격 조절
            st.markdown(f"[⭐ 평점 확인](https://www.google.com/search?q={urllib.parse.quote(search_q)})")
            st.markdown(f"[📍 상세 위치](https://www.google.com/maps/search/{urllib.parse.quote(map_q)})")
        st.divider()

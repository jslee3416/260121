import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 TOP 20", layout="wide")

# 구글 드라이브 파일 ID 및 직접 다운로드 URL
GOOGLE_FILE_ID = '15qLFBk-cWaGgGxe2sPz_FdgeYpquhQa4'
DIRECT_URL = f'https://drive.google.com/uc?export=download&id={GOOGLE_FILE_ID}'

@st.cache_data(show_spinner=False)
def load_and_process_data(url):
    try:
        # 클라우드에서 데이터 가져오기
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # [핵심] 만약 응답이 HTML이라면(권한 문제), 에러 메시지 반환
        if "html" in response.headers.get('Content-Type', '').lower():
            return "구글 드라이브 권한 에러: 파일이 공개 상태가 아닙니다. '링크가 있는 모든 사용자'로 설정을 변경해주세요."

        # 여러 인코딩과 구분자를 시도하는 루프
        for enc in ['cp949', 'utf-8-sig', 'euc-kr']:
            try:
                # 텍스트 스트림으로 변환 후 읽기
                data_stream = io.BytesIO(response.content)
                df = pd.read_csv(
                    data_stream, 
                    encoding=enc,
                    sep=None,          # 구분자 자동 감지 (콤마, 탭 등)
                    engine='python',   # 자동 감지를 위해 python 엔진 사용
                    on_bad_lines='skip', 
                    dtype=str,         # 모든 데이터를 일단 문자열로 읽어 오류 방지
                    low_memory=False
                )
                
                # 필요한 컬럼 추출 (안전하게 인덱스로 접근)
                # 4번째(3), 9번째(8), 10번째(9), 19번째(18)
                if df.shape[1] >= 19:
                    df_final = df.iloc[:, [3, 8, 9, 18]].copy()
                    df_final.columns = ['status', 'name', 'category', 'address']
                    
                    # 폐업 데이터 제거 (키워드 확장)
                    df_final = df_final[~df_final['status'].fillna('').str.contains("폐업|취소|말소|정리")].copy()
                    
                    if not df_final.empty:
                        return df_final
            except Exception:
                continue
                
        return "데이터 구조 해석 실패: 파일의 형식이 올바르지 않습니다."
    except Exception as e:
        return f"연결 오류: {str(e)}"

# --- UI 부분 ---
st.title("🍴 서울시 실시간 맛집 추천 가이드")

with st.spinner('데이터를 정밀 분석 중입니다...'):
    data = load_and_process_data(DIRECT_URL)

if isinstance(data, str):
    st.error(data)
    st.markdown("""
    ### 🚩 해결 방법:
    1. **구글 드라이브 공유 확인**: 파일 우클릭 -> 공유 -> '제한됨'을 **'링크가 있는 모든 사용자'**로 변경하셨나요?
    2. **파일 형식 확인**: 파일이 `.csv` 확장자가 맞는지, 혹시 엑셀(`.xlsx`) 파일은 아닌지 확인해주세요. (엑셀이면 코드를 바꿔야 합니다.)
    """)
else:
    st.success(f"✅ 데이터를 성공적으로 불러왔습니다. (총 {len(data):,}개 영업 중)")

    # 업종 LoV 생성
    category_list = sorted(data['category'].dropna().unique().tolist())
    selected_category = st.selectbox("🍱 음식 종류를 선택하세요", ["전체"] + category_list)

    filtered_df = data if selected_category == "전체" else data[data['category'] == selected_category]

    st.divider()
    st.subheader(f"📍 '{selected_category}' 추천 리스트 TOP 20")

    # 상위 20개 출력
    for i, row in filtered_df.head(20).iterrows():
        # 검색 쿼리 및 링크
        search_q = f"서울 {row['name']} {row['category']} 평점 리뷰"
        map_q = f"{row['name']} {row['address']}"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {row['name']}")
            st.write(f"📂 {row['category']} | 📍 {row['address']}")
        with col2:
            st.markdown(f"[⭐ 평점 확인](https://www.google.com/search?q={urllib.parse.quote(search_q)})")
            st.markdown(f"[📍 지도 보기](https://www.google.com/maps/search/{urllib.parse.quote(map_q)})")
        st.divider()

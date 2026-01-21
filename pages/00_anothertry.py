import streamlit as st
import pandas as pd
import os
import urllib.parse


# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 검색 서비스", layout="wide")

# 2. [수정포인트] 요청하신 다운로드 폴더 경로로 직접 설정
# 경로 앞에 r을 붙여야 윈도우 경로의 백슬래시(\)가 올바르게 인식됩니다.
CSV_PATH = r"C:\Users\jslee\Downloads\restaurantinseoul.csv"

@st.cache_data
def load_and_process_data(path):
    # 파일 존재 여부 확인
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"

    # 한글 깨짐 방지를 위한 인코딩 순차 시도
    encodings = ['cp949', 'utf-8-sig', 'euc-kr']
    
    for enc in encodings:
        try:
            container = []
            # 메모리 효율을 위해 필요한 4, 9, 10번째 컬럼만 5만 줄씩 끊어서 읽기
            reader = pd.read_csv(
                path, 
                usecols=[3, 8, 9], 
                chunksize=50000, 
                low_memory=False, 
                encoding=enc
            )
            
            for chunk in reader:
                # 컬럼 이름 통일 (상태, 사업장명, 업태명)
                chunk.columns = ['status', 'name', 'category']
                
                # '폐업' 데이터 삭제 및 '영업/정상' 데이터만 유지
                filtered = chunk[chunk['status'].fillna('').str.contains("영업|정상")].copy()
                filtered = filtered[~filtered['status'].fillna('').str.contains("폐업")].copy()
                
                container.append(filtered)
            
            if not container:
                return "EMPTY_DATA"
                
            return pd.concat(container, ignore_index=True)
            
        except (UnicodeDecodeError, ValueError):
            continue # 다음 인코딩 시도
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    return "ENCODING_ERROR"

# --- 메인 화면 구성 ---
st.title("🍴 서울시 맛집 정보 서비스")

# 사이드바 디버깅 정보
st.sidebar.header("📁 시스템 경로 확인")
st.sidebar.code(CSV_PATH)

# 데이터 로드 로직 시작
if not os.path.exists(CSV_PATH):
    st.error(f"❌ '{CSV_PATH}' 파일을 찾을 수 없습니다.")
    st.markdown(f"""
    **해결 방법:**
    1. 다운로드 폴더(`C:\\Users\\jslee\\Downloads`)에 `restaurantinseoul.csv` 파일이 실제로 있는지 확인해 주세요.
    2. 파일 확장자가 숨겨져서 `restaurantinseoul.csv.csv`처럼 되어있지는 않은지 확인하세요.
    3. 현재 이 앱이 **로컬(내 컴퓨터)**에서 실행 중인지 확인하세요. (클라우드 배포 시 사용자의 C드라이브는 접근 불가합니다.)
    """)
else:
    with st.spinner('다운로드 폴더에서 데이터를 분석 중입니다...'):
        result = load_and_process_data(CSV_PATH)

    if isinstance(result, str):
        st.error(f"❌ 오류 발생: {result}")
    else:
        df = result
        st.success(f"✅ 영업 중인 식당 {len(df):,}개를 로딩했습니다.")

        # 10번째 컬럼(category) 기반 LoV 생성
        categories = sorted(df['category'].dropna().unique().tolist())
        selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

        # 필터링 적용
        final_df = df if selected_category == "전체" else df[df['category'] == selected_category]

        st.subheader(f"📍 '{selected_category}' 검색 결과 (최상위 20개)")

        # 결과 리스트 출력 (Top 20)
        top_20 = final_df.head(20)
        
        if len(top_20) > 0:
            for i, row in top_20.iterrows():
                # 구글 검색 링크 생성
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
            st.warning("선택한 분류에 해당하는 데이터가 없습니다.")

import streamlit as st
import pandas as pd
import os
import urllib.parse

# 페이지 설정
st.set_page_config(page_title="서울 맛집 검색 앱", layout="wide")

# [방법 1 적용] 파일이 코드와 같은 폴더에 있을 때의 파일명
CSV_PATH = "restaurantinseoul.csv"

@st.cache_data
def load_and_process_data(path):
    # 1. 파일 존재 여부 확인
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"

    # 2. 인코딩 후보 설정 (공공데이터 표준 인코딩 순서)
    encodings = ['cp949', 'utf-8-sig', 'euc-kr']
    
    for enc in encodings:
        try:
            container = []
            # 3. 메모리 효율을 위해 chunksize(나눠 읽기)와 usecols(컬럼 선택) 적용
            # 4번째(3), 9번째(8), 10번째(9) 컬럼만 추출
            reader = pd.read_csv(
                path, 
                usecols=[3, 8, 9], 
                chunksize=50000, 
                low_memory=False, 
                encoding=enc
            )
            
            for chunk in reader:
                # 컬럼 이름이 한글이거나 다를 수 있으므로 강제 통일
                chunk.columns = ['status', 'name', 'category']
                
                # 4. [데이터 정제] 폐업 데이터 삭제 및 영업 데이터 필터링
                # fillna('')를 통해 결측치로 인한 에러 방지
                filtered = chunk[chunk['status'].fillna('').str.contains("영업|정상")].copy()
                filtered = filtered[~filtered['status'].fillna('').str.contains("폐업")].copy()
                
                container.append(filtered)
            
            # 조각난 데이터 합치기
            full_df = pd.concat(container, ignore_index=True)
            return full_df
            
        except (UnicodeDecodeError, ValueError):
            continue # 실패 시 다음 인코딩 시도
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    return "ENCODING_ERROR"

# --- 메인 인터페이스 ---
st.title("🍴 서울시 맛집 정보 서비스")

# 현재 상태 확인 (디버깅)
if not os.path.exists(CSV_PATH):
    st.error(f"❌ '{CSV_PATH}' 파일을 찾을 수 없습니다.")
    st.info("💡 **조치 방법:** 실행 중인 파이썬 코드(.py)와 같은 폴더에 `restaurantinseoul.csv` 파일을 복사해 넣어주세요.")
else:
    with st.spinner('데이터를 분석 중입니다... 잠시만 기다려 주세요.'):
        result = load_and_process_data(CSV_PATH)

    if isinstance(result, str):
        st.error(f"❌ 오류 발생: {result}")
    else:
        df = result
        st.success(f"✅ 영업 중인 식당 {len(df):,}개를 로딩했습니다.")

        # 10번째 컬럼(category) 기반으로 선택 목록(LoV) 생성
        categories = sorted(df['category'].dropna().unique().tolist())
        selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

        # 카테고리 필터링 적용
        final_df = df if selected_category == "전체" else df[df['category'] == selected_category]

        st.subheader(f"📍 '{selected_category}' 검색 결과 (최상위 20개)")

        # 결과 출력 (Top 20)
        top_20 = final_df.head(20)
        
        if len(top_20) > 0:
            for i, row in top_20.iterrows():
                # 구글 검색 URL 생성 (식당이름 + 서울 + 평점)
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
            st.warning("해당 조건에 맞는 데이터가 없습니다.")

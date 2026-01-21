import streamlit as st
import pandas as pd
import os
import urllib.parse

# 페이지 설정
st.set_page_config(page_title="서울 맛집 데이터 분석", layout="wide")

# 1. 파일 경로 설정 (슬래시를 사용하여 윈도우 경로 오류 방지)
CSV_PATH = "C:/Users/jslee/Downloads/restaurantinseoul.csv"

@st.cache_data
def load_and_process_data(path):
    # [체크 1] 파일이 물리적으로 존재하는지 확인
    if not os.path.exists(path):
        return "FILE_NOT_FOUND"

    # [체크 2] 한글 인코딩 시도 (공공데이터는 보통 cp949나 euc-kr입니다)
    encodings = ['cp949', 'utf-8-sig', 'euc-kr']
    
    for enc in encodings:
        try:
            # 대용량 처리를 위해 chunksize 사용
            # 필요한 컬럼: 4번째(3), 9번째(8), 10번째(9)
            container = []
            reader = pd.read_csv(
                path, 
                usecols=[3, 8, 9], 
                chunksize=50000, 
                low_memory=False, 
                encoding=enc
            )
            
            for chunk in reader:
                # 컬럼명 강제 지정
                chunk.columns = ['status', 'name', 'category']
                
                # [필터링] '폐업' 문구가 들어간 행 삭제
                # 결측치(NaN) 제거 후 문자열 포함 여부 확인
                filtered_chunk = chunk[chunk['status'].fillna('').str.contains("영업|정상")].copy()
                filtered_chunk = filtered_chunk[~filtered_chunk['status'].fillna('').str.contains("폐업")].copy()
                
                container.append(filtered_chunk)
            
            # 모든 조각 합치기
            full_df = pd.concat(container, ignore_index=True)
            return full_df
            
        except (UnicodeDecodeError, ValueError):
            continue # 인코딩이나 컬럼 인덱스가 안 맞으면 다음 시도
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    return "ENCODING_ERROR"

# --- 메인 실행부 ---
st.title("🍴 서울시 맛집 정보 서비스")
st.info(f"📁 대상 파일: {CSV_PATH}")

# 데이터 로딩 시작
with st.spinner('데이터를 분석 중입니다... 잠시만 기다려 주세요.'):
    result = load_and_process_data(CSV_PATH)

# 에러 처리 및 화면 구성
if isinstance(result, str):
    if result == "FILE_NOT_FOUND":
        st.error(f"❌ 파일을 찾을 수 없습니다. 경로를 확인해주세요: {CSV_PATH}")
    elif result == "ENCODING_ERROR":
        st.error("❌ 파일 읽기에 실패했습니다. 인코딩 형식이 맞지 않거나 컬럼 구성이 다릅니다.")
    else:
        st.error(f"❌ 알 수 없는 에러가 발생했습니다: {result}")
else:
    df = result
    st.success(f"✅ 영업 중인 식당 {len(df):,}개를 로딩했습니다.")

    # 10번째 컬럼(category) 기반 LoV 생성
    # 결측치 제거 후 정렬
    categories = sorted(df['category'].dropna().unique().tolist())
    
    # 사이드바에서 카테고리 선택
    selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

    # 필터링 적용
    if selected_category != "전체":
        final_df = df[df['category'] == selected_category]
    else:
        final_df = df

    st.subheader(f"📍 '{selected_category}' 검색 결과 (최상위 20개)")

    # 결과 출력
    top_20 = final_df.head(20)
    
    if len(top_20) > 0:
        for i, row in top_20.iterrows():
            # 구글 검색 URL 생성 (식당이름 + 업태)
            search_query = urllib.parse.quote(f"서울 {row['name']} {row['category']}")
            google_url = f"https://www.google.com/search?q={search_query}"
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{i+1}. {row['name']}** \n({row['category']})")
                col2.markdown(f"[⭐ 구글검색]({google_url})")
                st.divider()
    else:
        st.warning("선택한 카테고리에 해당하는 데이터가 없습니다.")

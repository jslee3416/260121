import streamlit as st
import pandas as pd
import os
import urllib.parse

# 페이지 설정
st.set_page_config(page_title="서울 식당 분석 앱", layout="wide")

# 1. 파일 경로 및 설정
FILE_PATH = r"C:\Users\jslee\Downloads\restaurantinseoul.csv"

@st.cache_data
def load_and_process_data(path):
    if not os.path.exists(path):
        return None
    
    # 메모리 절약을 위해 필요한 컬럼 인덱스만 먼저 정의
    # 4번째(index 3), 9번째(index 8), 10번째(index 9) 등
    # 실제 데이터의 컬럼 순서에 맞춰 index를 조정하세요.
    try:
        # 데이터 로딩
        df = pd.read_csv(path, low_memory=False)
        
        # 컬럼 이름이 명확하지 않을 수 있으므로 인덱스로 접근
        # 컬럼 인덱스는 0부터 시작하므로:
        # 4번째 컬럼: df.iloc[:, 3] (영업상태)
        # 9번째 컬럼: df.iloc[:, 8] (사업장명)
        # 10번째 컬럼: df.iloc[:, 9] (업태명/분류)
        
        status_col = df.columns[3]
        name_col = df.columns[8]
        category_col = df.columns[9]
        
        # (1) 4번째 컬럼에서 '폐업' 데이터 삭제 (영업 중인 데이터만 유지)
        df = df[df[status_col].str.contains("영업|정상", na=False)]
        df = df[~df[status_col].str.contains("폐업", na=False)]
        
        return df, name_col, category_col
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return None, None, None

# 2. 데이터 불러오기
data_bundle = load_and_process_data(FILE_PATH)
df, name_col, category_col = data_bundle

if df is not None:
    st.title("🍴 서울시 맛집 정보 조회 (영업 중)")

    # 3. 10번째 컬럼을 기반으로 LoV (Selectbox) 만들기
    categories = sorted(df[category_col].unique().tolist())
    selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", ["전체"] + categories)

    # 카테고리 필터링
    if selected_category != "전체":
        filtered_df = df[df[category_col] == selected_category]
    else:
        filtered_df = df

    # 4. 구글 맵 연결 및 평점순 정렬 시뮬레이션
    # 실제 CSV에는 구글 평점이 없을 가능성이 높으므로, 
    # 구글 검색 링크를 생성하고 리스트를 보여줍니다.
    
    st.subheader(f"📍 '{selected_category}' 검색 결과 (Top 20)")
    
    # 상위 20개만 추출
    top_20 = filtered_df.head(20).copy()
    
    # 구글 맵 검색 URL 생성 함수
    def make_google_maps_link(row):
        shop_name = row[name_col]
        # '서울 사업장명'으로 검색 쿼리 생성
        query = urllib.parse.quote(f"서울 {shop_name} 평점")
        return f"https://www.google.com/maps/search/{query}"

    # 결과 출력
    for i, (idx, row) in enumerate(top_20.iterrows()):
        col1, col2 = st.columns([3, 1])
        shop_name = row[name_col]
        map_url = make_google_maps_link(row)
        
        with col1:
            st.markdown(f"**{i+1}. {shop_name}** ({row[category_col]})")
            # 주소 정보가 10번째 이후에 있다면 추가 표시 가능 (예: index 18~19번쯤의 도로명 주소)
            # st.caption(f"주소: {row.iloc[18]}") 
            
        with col2:
            st.write(f"[⭐ 구글맵 확인]({map_url})")
            
    if len(top_20) == 0:
        st.info("해당 조건의 데이터가 없습니다.")

else:
    st.error("파일을 불러올 수 없습니다. 경로와 파일명을 확인해주세요.")

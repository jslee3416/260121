import streamlit as st
import pandas as pd
import os
import urllib.parse

st.set_page_config(page_title="서울 맛집 검색", layout="wide")

# 1. 파일 경로 설정
CSV_PATH = r"C:\Users\jslee\Downloads\restaurantinseoul.csv"

@st.cache_data
def load_and_filter_data(path):
    if not os.path.exists(path):
        return None
    
    container = []
    # progress_bar로 진행 상황 시각화
    progress_text = "데이터를 한 조각씩 불러오는 중입니다..."
    my_bar = st.progress(0, text=progress_text)
    
    # [핵심] chunksize를 지정하여 데이터를 나누어 읽음 (메모리 과부하 방지)
    # 149MB 기준 약 7~10개 조각으로 나누어 처리
    total_chunks = 10 
    
    try:
        # 필요한 컬럼(3, 8, 9번)만 지정해서 읽기
        reader = pd.read_csv(
            path, 
            usecols=[3, 8, 9], 
            chunksize=20000, 
            low_memory=False, 
            encoding='cp949' # 한글 깨짐 방지 (필요 시 utf-8로 변경)
        )
        
        for i, chunk in enumerate(reader):
            # 컬럼명 통일
            chunk.columns = ['status', 'name', 'category']
            
            # 읽자마자 '폐업' 데이터 삭제 (데이터 다이어트)
            filtered_chunk = chunk[~chunk['status'].str.contains("폐업", na=False)].copy()
            container.append(filtered_chunk)
            
            # 진행바 업데이트
            progress = min((i + 1) / total_chunks, 1.0)
            my_bar.progress(progress, text=f"{progress_text} ({i+1}번 조각 처리 중)")
            
        my_bar.empty() # 작업 완료 후 진행바 제거
        return pd.concat(container, ignore_index=True)
    
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# 2. 데이터 실행
df = load_and_filter_data(CSV_PATH)

if df is not None:
    st.title("🍴 서울시 맛집 정보 서비스")
    st.caption(f"영업 중인 식당 {len(df):,}개를 로딩 완료했습니다.")

    # 3. LoV (10번째 컬럼이었던 'category')
    categories = sorted(df['category'].unique().tolist())
    selected_category = st.selectbox("🎯 음식 종류(업태)를 선택하세요", categories)

    # 4. 필터링 및 결과 출력
    if selected_category:
        result_df = df[df['category'] == selected_category].head(20)
        
        st.subheader(f"📍 '{selected_category}' 검색 결과 Top 20")
        
        for i, row in result_df.iterrows():
            # 구글 검색 링크 생성
            query = urllib.parse.quote(f"서울 {row['name']} {selected_category} 평점")
            search_url = f"https://www.google.com/search?q={query}"
            
            with st.container():
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{row['name']}**")
                col2.markdown(f"[⭐ 평점확인]({search_url})")
                st.divider() # 구분선
else:
    st.info("데이터 파일을 읽어오는 데 실패했습니다. 파일 경로를 확인해 주세요.")

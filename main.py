import streamlit as st
import pandas as pd
import urllib.parse
import os

st.set_page_config(page_title="서울 맛집 파인더", layout="wide")

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_and_clean_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            st.error(f"파일 없음: {file_name}")
            return pd.DataFrame()

        # 1. 인코딩 시도 (한글 깨짐 방지 최적화)
        df = None
        for enc in ['cp949', 'utf-8-sig', 'utf-8', 'euc-kr']:
            try:
                # 구분자 자동 감지 및 공백 제거(skipinitialspace) 적용
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python', skipinitialspace=True)
                if df is not None and not df.empty:
                    # 컬럼명의 앞뒤 공백 제거
                    df.columns = df.columns.str.strip()
                    break
            except:
                continue
        
        if df is None or df.empty:
            return pd.DataFrame()

        # [디버깅 정보] 사이드바에 실제 읽어온 컬럼명을 출력합니다.
        st.sidebar.info(f"📂 감지된 컬럼명: {df.columns.tolist()}")

        # 2. 식당명 컬럼 타겟팅
        # '식당명'을 최우선으로 찾고, 없으면 유사한 이름을 찾습니다.
        target_name_col = next((c for c in df.columns if c == '식당명'), 
                          next((c for c in df.columns if '식당' in c or '상호' in c), df.columns[0]))
        
        target_area_col = next((c for c in df.columns if '지역' in c or '주소' in c), 
                          df.columns[1] if len(df.columns) > 1 else df.columns[0])
        
        target_menu_col = next((c for c in df.columns if '메뉴' in c), None)

        # 데이터 재구성
        rename_dict = {target_name_col: '상호', target_area_col: '지역'}
        if target_menu_col:
            rename_dict[target_menu_col] = '메뉴'
            
        df = df[list(rename_dict.keys())].rename(columns=rename_dict)
        
        # 3. 행정구역(구/동) 분리 로직
        def split_region(x):
            if pd.isna(x): return "미분류", "미분류"
            parts = str(x).strip().split()
            gu = parts[0] if len(parts) > 0 else "미분류"
            dong = " ".join(parts[1:]) if len(parts) > 1 else "전체"
            return gu, dong

        df[['구', '동']] = df['지역'].apply(lambda x: pd.Series(split_region(x)))
        
        return df.dropna(subset=['상호']).reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame()

df = load_and_clean_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")

if not df.empty:
    st.sidebar.success("✅ '식당명' 데이터를 성공적으로 연결했습니다!")
    
    # 지역 필터
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    dong_options = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", ["전체"] + dong_options)
    
    filtered_df = df[df['구'] == selected_gu]
    if selected_dong != "전체":
        filtered_df = filtered_df[filtered_df['동'] == selected_dong]

    # 검색 기능
    search_query = st.sidebar.text_input("🔍 식당 이름 검색", "")
    if search_query:
        filtered_df = filtered_df[filtered_df['상호'].str.contains(search_query, na=False)]

    st.subheader(f"📍 {selected_gu} {selected_dong if selected_dong != '전체' else ''} 맛집 목록")

    if not filtered_df.empty:
        # 페이지네이션
        rows_per_page = 15
        total_pages = max(len(filtered_df) // rows_per_page + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
        current_page = st.number_input(f"페이지 (1/{total_pages})", 1, total_pages, 1)
        
        start_idx = (current_page - 1) * rows_per_page
        page_data = filtered_df.iloc[start_idx : start_idx + rows_per_page].copy()

        # 테이블 출력
        st.markdown("---")
        st.markdown("| 번호 | 식당명 | 지역(구/동) | 실시간 구글 평점 링크 |")
        st.markdown("| :--- | :--- | :--- | :--- |")
        
        for i, (_, row) in enumerate(page_data.iterrows()):
            # 구글 검색 정확도를 위해 구+동+식당명 조합
            search_query = f"{row['구']} {row['동']} {row['상호']}"
            google_url = f"https://www.google.com/maps/search/{urllib.parse.quote(search_query)}"
            
            menu_info = f" ({row['메뉴']})" if '메뉴' in row and pd.notna(row['메뉴']) else ""
            st.markdown(f"| {start_idx + i + 1} | **{row['상호']}**{menu_info} | {row['구']} {row['동']} | [⭐ 평점 확인하기]({google_url}) |")
    else:
        st.warning("선택하신 조건에 해당하는 식당이 없습니다.")
else:
    st.error("데이터를 불러올 수 없습니다.")
    st.info("파일의 첫 줄에 '식당명'이라는 컬럼 제목이 있는지 확인해 주세요.")

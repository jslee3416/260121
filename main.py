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

        # 1. 인코딩 및 구분자 자동 감지 로직
        df = None
        for enc in ['cp949', 'utf-8', 'euc-kr', 'utf-8-sig']:
            try:
                # sep=None, engine='python'은 쉼표/탭/세미콜론 자동 감지
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                if df is not None and not df.empty:
                    # 빈 칸(Unnamed) 컬럼 제거 및 정리
                    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                    break
            except:
                continue
        
        if df is None or df.empty:
            return pd.DataFrame()

        # [진단용] 실제 파일의 컬럼명을 사용자에게 보여줌
        actual_columns = df.columns.tolist()
        st.sidebar.info(f"🔍 파일 내 실제 컬럼명: {actual_columns}")

        # 2. 유연한 컬럼 매칭 (이름이 조금 달라도 찾아냄)
        # 상호명 후보: 식당명, 상호명, 상호, 업소명, 식당(ID)
        # 지역명 후보: 지역명, 지역, 주소, 소재지, 자치구명
        name_map = {}
        cols = df.columns
        
        name_map['상호'] = next((c for c in cols if c in ['식당명', '상호명', '상호', '업소명', '식당(ID)']), None)
        name_map['지역'] = next((c for c in cols if c in ['지역명', '지역', '주소', '소재지', '자치구명', '지역명 ']), None)
        name_map['메뉴'] = next((c for c in cols if c in ['대표메뉴명', '대표메뉴', '메뉴', '주요메뉴']), None)

        # 필수 컬럼(상호, 지역)이 없으면 첫 번째, 두 번째 컬럼을 강제로 할당
        if not name_map['상호']: name_map['상호'] = cols[0]
        if not name_map['지역']: name_map['지역'] = cols[1] if len(cols) > 1 else cols[0]

        # 데이터 재구성
        final_cols = [v for v in name_map.values() if v is not None]
        inv_map = {v: k for k, v in name_map.items() if v is not None}
        
        df = df[final_cols].rename(columns=inv_map)
        
        # 3. 행정구역 분리
        def split_region(x):
            if pd.isna(x): return "미분류", "미분류"
            parts = str(x).strip().split()
            gu = parts[0] if len(parts) > 0 else "미분류"
            dong = " ".join(parts[1:]) if len(parts) > 1 else "전체"
            return gu, dong

        df[['구', '동']] = df['지역'].apply(lambda x: pd.Series(split_region(x)))
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame()

df = load_and_clean_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")

if not df.empty:
    st.sidebar.success("✅ 데이터를 성공적으로 불러왔습니다!")
    
    # 지역 필터
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    dong_options = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", ["전체"] + dong_options)
    
    filtered_df = df[df['구'] == selected_gu]
    if selected_dong != "전체":
        filtered_df = filtered_df[filtered_df['동'] == selected_dong]

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
            query = urllib.parse.quote(f"{row['구']} {row['동']} {row['상호']}")
            google_url = f"https://www.google.com/maps/search/{query}"
            st.markdown(f"| {start_idx + i + 1} | **{row['상호']}** | {row['구']} {row['동']} | [⭐ 평점 확인하기]({google_url}) |")
    else:
        st.warning("조건에 맞는 식당이 없습니다.")
else:
    st.error("데이터를 분석할 수 없습니다.")
    st.info("사이드바에 표시된 '파일 내 실제 컬럼명'을 확인해 보세요.")

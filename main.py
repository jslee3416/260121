import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 평점 가이드", layout="wide")

DATA_FILE = "restaurants.csv"

@st.cache_data
def load_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()

        # 인코딩 대응
        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                # low_memory=False로 대용량 대응, 순서 기반 접근을 위해 그대로 로드
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty:
                    break
            except:
                continue
        
        if df is None: return pd.DataFrame()

        # [핵심] 순서(인덱스) 기반 컬럼 추출
        # 0번: 식당ID, 1번: 식당명, 4번(또는 마지막): 지역명
        id_col = df.columns[0]
        name_col = df.columns[1]
        # 지역명은 데이터 구조상 보통 4번째 이후에 있으므로 안전하게 검색 혹은 마지막 선택
        area_col = next((c for c in df.columns if '지역' in str(c) or '주소' in str(c)), df.columns[-1])

        # 필요한 컬럼만 슬림하게 복사
        new_df = df[[id_col, name_col, area_col]].copy()
        new_df.columns = ['ID', '상호', '지역']
        
        # '구' 정보 추출 (지역명의 첫 단어)
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 매칭 오류: {e}")
        return pd.DataFrame()

df = load_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.markdown("##### 📍 자치구를 선택하면 해당 지역의 주요 식당 20곳을 보여드립니다.")

if not df.empty:
    # 사이드바 필터
    st.sidebar.header("📍 지역 필터")
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    # 해당 구의 상위 20개 식당 필터링
    filtered_df = df[df['구'] == selected_gu].head(20)

    # 3. 카드형 레이아웃 출력
    st.markdown("---")
    cols = st.columns(2) # 2열 배치
    
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 2]:
            # 검색 정확도를 위해 [지역명 + 상호] 조합 사용
            # 식당 ID는 내부 식별용으로만 유지하고 검색 쿼리에는 지역/상호를 사용합니다.
            search_query = f"{row['지역']} {row['상호']} 평점"
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            
            # 디자인 적용된 카드 섹션
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e0e0; 
                padding: 20px; 
                border-radius: 15px; 
                margin-bottom: 20px; 
                background-color: #ffffff;
                box-shadow: 4px 4px 12px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3 style="margin: 0; color: #1A73E8; font-size: 1.25em;">{row['상호']}</h3>
                    <span style="font-size: 0.75em; color: #999;">ID: {row['ID']}</span>
                </div>
                <p style="font-size: 0.9em; color: #5F6368; margin: 10px 0 20px 0;">📍 {row['지역']}</p>
                <a href="{google_url}" target="_blank" style="text-decoration: none;">
                    <div style="
                        display: block;
                        background-color: #4285F4; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 8px; 
                        font-weight: bold;
                        text-align: center;
                        transition: 0.3s;
                    ">
                        ⭐ 구글 평점 및 리뷰 확인하기
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("데이터를 로드하는 중 컬럼 매칭에 실패했습니다. CSV 파일의 형식을 다시 확인해주세요.")

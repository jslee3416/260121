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

        # 인코딩 시도
        df = None
        for enc in ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']:
            try:
                # header=0으로 첫 줄을 읽고, 데이터는 이후부터 가져옴
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty:
                    break
            except:
                continue
        
        if df is None: return pd.DataFrame()

        # [수정] 컬럼 순서 기반 추출 (두 번째 컬럼 = 인덱스 1)
        # 사용자의 요청에 따라 2번째 컬럼(index 1)을 식당명으로 고정
        name_col = df.columns[1] 
        # 지역명은 보통 4번째(index 3) 혹은 마지막 근처에 있음 (안전하게 이름 검색 후 안되면 마지막 선택)
        area_col = next((c for c in df.columns if '지역' in str(c) or '주소' in str(c)), df.columns[-1])

        new_df = df[[name_col, area_col]].copy()
        new_df.columns = ['상호', '지역']
        
        # '구' 정보 추출 (지역명의 첫 단어)
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
        
    except:
        return pd.DataFrame()

df = load_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.markdown("##### 📍 자치구를 선택하면 가장 인기 있는 식당 20곳의 평점을 확인할 수 있습니다.")

if not df.empty:
    # 사이드바 필터
    st.sidebar.header("📍 지역 필터")
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    # 해당 구의 상위 20개 식당 슬림화
    filtered_df = df[df['구'] == selected_gu].head(20)

    # 3. 카드형 레이아웃 출력
    st.markdown("---")
    
    # 2열로 나누어 배치
    cols = st.columns(2)
    
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 2]:
            # 구글 검색 키워드: 지역명 + 식당명 + 평점
            search_query = f"{row['지역']} {row['상호']} 평점"
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            
            # 디자인 적용된 카드 섹션
            st.markdown(f"""
            <div style="
                border: 1px solid #eee; 
                padding: 20px; 
                border-radius: 12px; 
                margin-bottom: 15px; 
                background-color: white;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            ">
                <h3 style="margin: 0; color: #1A73E8; font-size: 1.2em;">{i+1}. {row['상호']}</h3>
                <p style="font-size: 0.85em; color: #5F6368; margin: 8px 0 15px 0;">📍 {row['지역']}</p>
                <a href="{google_url}" target="_blank" style="text-decoration: none;">
                    <div style="
                        display: inline-block;
                        background-color: #4285F4; 
                        color: white; 
                        padding: 8px 16px; 
                        border-radius: 6px; 
                        font-weight: bold;
                        font-size: 0.9em;
                        text-align: center;
                    ">
                        ⭐ 실시간 평점/리뷰 확인하기
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("데이터를 읽어올 수 없습니다. 'restaurants.csv' 파일의 구성을 확인해주세요.")

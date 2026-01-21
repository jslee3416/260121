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
        for enc in ['utf-8-sig', 'cp949', 'utf-8']:
            try:
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip', low_memory=False)
                if df is not None and not df.empty:
                    df.columns = [str(c).strip() for c in df.columns]
                    break
            except:
                continue
        
        if df is None: return pd.DataFrame()

        # 컬럼 매칭 (식당명, 지역명만 추출)
        name_col = next((c for c in df.columns if '식당' in c or '상호' in c), df.columns[0])
        area_col = next((c for c in df.columns if '지역' in c or '주소' in c), df.columns[-1])

        new_df = df[[name_col, area_col]].copy()
        new_df.columns = ['상호', '지역']
        
        # '구' 정보 추출
        new_df['구'] = new_df['지역'].apply(lambda x: str(x).split()[0] if pd.notna(x) else "서울")
        
        return new_df.dropna(subset=['상호']).reset_index(drop=True)
        
    except:
        return pd.DataFrame()

df = load_data(DATA_FILE)

# 2. UI 구성
st.title("🍴 서울 맛집 실시간 평점 가이드")
st.markdown("##### 📍 현재 위치에서 가장 인기 있는 식당의 평점을 확인하세요.")

if not df.empty:
    # 사이드바 필터
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    # 해당 구의 식당 20개 추출 (데이터상 상단 20개)
    filtered_df = df[df['구'] == selected_gu].head(20)

    st.info(f"💡 **{selected_gu}**의 주요 식당 20곳입니다. 클릭 시 실시간 구글 평점으로 연결됩니다.")

    # 3. 카드형 레이아웃으로 출력 (평점 강조형)
    st.markdown("---")
    
    # 2열 레이아웃
    cols = st.columns(2)
    
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        with cols[i % 2]:
            # 구글 검색 쿼리 (주소 + 식당명 + 평점)
            search_query = f"{row['지역']} {row['상호']} 평점"
            google_search_url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            
            # 카드 디자인
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9;">
                    <h4 style="margin: 0; color: #333;">{i+1}. {row['상호']}</h4>
                    <p style="font-size: 0.9em; color: #666; margin: 5px 0;">{row['지역']}</p>
                    <a href="{google_search_url}" target="_blank" style="text-decoration: none;">
                        <button style="background-color: #4285F4; color: white; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer;">
                            ⭐ 실시간 평점/리뷰 확인
                        </button>
                    </a>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")

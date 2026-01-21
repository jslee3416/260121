import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울관광재단 맛집 가이드", layout="wide")

@st.cache_data
def load_and_clean_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 파일 존재 및 크기 체크
        if not os.path.exists(file_path):
            st.error(f"파일을 찾을 수 없습니다: {file_name}")
            return pd.DataFrame()
        
        # 인코딩 및 구분자 자동 감지 로직 (에러 방지 핵심)
        df = None
        for enc in ['cp949', 'utf-8', 'euc-kr']:
            try:
                # sep=None, engine='python'은 쉼표/탭/세미콜론 등을 자동 감지함
                df = pd.read_csv(file_path, encoding=enc, sep=None, engine='python')
                if df is not None and not df.empty:
                    break
            except:
                continue
        
        if df is None or df.empty:
            return pd.DataFrame()

        # [서울관광재단 데이터 컬럼 매칭]
        cols = df.columns.tolist()
        name_variants = {
            '상호': ['상호명', '상호', 'POST_SJ', 'FACILITY_NM', '업소명'],
            '구': ['자치구명', '구', 'SIGUNGU_NM', 'ADDR_NM', '주소', '시군구명'],
            '동': ['법정동명', '동', 'DONG_NM', '행정동명', '행정동'],
            '위도': ['위도', '좌표_Y', 'LAT', 'Y_COORD', 'LATITUDE', 'y'],
            '경도': ['경도', '좌표_X', 'LOT', 'X_COORD', 'LONGITUDE', 'x']
        }
        
        actual_map = {}
        for key, variants in name_variants.items():
            match = next((c for c in cols if c in variants), None)
            if match:
                actual_map[match] = key
        
        # 필수 정보(위도/경도)가 없으면 중단
        if '위도' not in actual_map.values() or '경도' not in actual_map.values():
            st.warning(f"위도/경도 컬럼을 찾을 수 없습니다. (현재 컬럼명: {cols})")
            return pd.DataFrame()

        # 데이터 정제
        df = df[list(actual_map.keys())].rename(columns=actual_map)
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        
        # 유효한 좌표만 남기기
        df = df.dropna(subset=['위도', '경도'])
        df = df[(df['위도'] > 33) & (df['위도'] < 39) & (df['경도'] > 124) & (df['경도'] < 132)]
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return pd.DataFrame()

# 서울관광재단 데이터 파일 호출
DATA_FILE = "서울관광재단_식당운영정보_20230111.csv"
df = load_and_clean_data(DATA_FILE)

# 2. 메인 UI 구성
if not df.empty:
    st.sidebar.title("📍 지역 선택")
    
    # 지역 리스트 생성 (비어있는 값 제외)
    gu_list = sorted(df['구'].dropna().unique())
    selected_gu = st.sidebar.selectbox("구 선택", gu_list)
    
    dong_list = sorted(df[df['구'] == selected_gu]['동'].dropna().unique())
    selected_dong = st.sidebar.selectbox("동 선택", dong_list)
    
    # 필터링
    filtered_df = df[(df['구'] == selected_gu) & (df['동'] == selected_dong)]
    
    st.title(f"🍴 서울관광재단 추천: {selected_gu} {selected_dong} 식당")
    st.info(f"검색된 식당: {len(filtered_df)}개 (마커를 올려 구글 평점을 확인하세요)")

    # 3. 페이지네이션 (상위 20개씩 표시)
    rows_per_page = 20
    total_pages = max((len(filtered_df) // rows_per_page) + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
    current_page = st.sidebar.number_input(f"페이지 (1-{total_pages})", 1, total_pages, 1)
    page_df = filtered_df.iloc[(current_page-1)*rows_per_page : current_page*rows_per_page]

    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("📋 현재 페이지 목록")
        st.dataframe(page_df[['상호']], use_container_width=True, height=500)

    with col2:
        if not page_df.empty:
            # 지도 렌더링
            m = folium.Map(location=[page_df['위도'].mean(), page_df['경도'].mean()], zoom_start=15)
            cluster = MarkerCluster().add_to(m)
            
            for _, row in page_df.iterrows():
                # 구글 맵 검색 URL 생성 (인코딩 포함)
                query = urllib.parse.quote(f"{selected_gu} {row['상호']}")
                google_url = f"https://www.google.com/maps/search/{query}"
                
                # 툴팁 HTML: 마우스를 올리면 나타남
                tooltip_html = f"""
                <div style="font-family: sans-serif; width: 200px; padding: 5px;">
                    <h4 style="margin:0 0 10px 0;">{row['상호']}</h4>
                    <p style="font-size:12px; margin-bottom:10px;">서울관광재단 인증 식당</p>
                    <a href="{google_url}" target="_blank" 
                       style="display:block; text-align:center; background:#4285F4; color:white; 
                              padding:8px; border-radius:5px; text-decoration:none; font-weight:bold;">
                        구글맵에서 평점 보기 ↗
                    </a>
                </div>
                """
                
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    tooltip=folium.Tooltip(tooltip_html, sticky=False),
                    icon=folium.Icon(color='red', icon='utensils', prefix='fa')
                ).add_to(cluster)
            
            st_folium(m, width="100%", height=550, key=f"map_{current_page}")
        else:
            st.warning("표시할 식당 데이터가 없습니다.")
else:
    st.error("데이터 로드에 실패했습니다.")
    st.markdown(f"**확인 사항:** GitHub에 `{DATA_FILE}` 파일이 업로드되어 있는지, 파일 내용이 비어있지 않은지 확인해 주세요.")

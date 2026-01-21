import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os
import urllib.parse

# 1. 페이지 설정
st.set_page_config(page_title="서울 맛집 구글맵 가이드", layout="wide")

@st.cache_data
def load_and_clean_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 인코딩 처리
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        # [수정] 실제 데이터의 컬럼명을 확인하여 매칭 (후보군 대폭 강화)
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
        
        # 필수 컬럼 존재 확인
        if '위도' not in actual_map.values() or '경도' not in actual_map.values():
            st.error(f"파일에서 위도/경도 컬럼을 찾을 수 없습니다. 현재 컬럼명: {cols}")
            return pd.DataFrame()

        # 데이터 필터링 및 이름 변경
        df = df[list(actual_map.keys())].rename(columns=actual_map)
        
        # [핵심] 위도/경도 숫자 변환 및 오류 데이터(문자 등) 제거
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        
        # 좌표값이 없거나(NaN), 0이거나, 범위를 벗어난 데이터 삭제
        df = df.dropna(subset=['위도', '경도'])
        df = df[(df['위도'] > 33) & (df['위도'] < 39) & (df['경도'] > 124) & (df['경도'] < 132)]
        
        return df.reset_index(drop=True)
        
    except Exception as e:
        st.error(f"데이터 로드 중 치명적 오류 발생: {e}")
        return pd.DataFrame()

# 파일명 호출
DATA_FILE = "서울관광재단_식당운영정보_20230111.csv"
df = load_and_clean_data(DATA_FILE)

# 2. 메인 UI
if not df.empty:
    st.sidebar.title("📍 지역 선택")
    
    # 구/동 선택 (결측치 제거 후 리스트 생성)
    gu_list = sorted(df['구'].dropna().unique())
    selected_gu = st.sidebar.selectbox("구 선택", gu_list)
    
    dong_list = sorted(df[df['구'] == selected_gu]['동'].dropna().unique())
    selected_dong = st.sidebar.selectbox("동 선택", dong_list)
    
    # 필터링
    filtered_df = df[(df['구'] == selected_gu) & (df['동'] == selected_dong)]
    
    st.title(f"🍴 {selected_gu} {selected_dong} 식당 리스트")
    st.info(f"선택 지역 식당: {len(filtered_df)}개 (마커를 클릭해 구글 평점을 확인하세요)")

    # 페이지네이션
    rows_per_page = 20
    total_pages = max(len(filtered_df) // rows_per_page + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
    current_page = st.sidebar.number_input(f"페이지 (1-{total_pages})", 1, total_pages, 1)
    page_df = filtered_df.iloc[(current_page-1)*rows_per_page : current_page*rows_per_page]

    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("📋 목록")
        st.dataframe(page_df[['상호']], use_container_width=True, height=500)

    with col2:
        if not page_df.empty:
            # 지도 중심 (현재 페이지 식당들의 평균 위치)
            m = folium.Map(location=[page_df['위도'].mean(), page_df['경도'].mean()], zoom_start=15)
            cluster = MarkerCluster().add_to(m)
            
            for _, row in page_df.iterrows():
                # 구글 맵 검색 링크 생성 (식당 이름과 구 이름을 합쳐서 검색 정확도 향상)
                query = urllib.parse.quote(f"{selected_gu} {row['상호']}")
                google_map_url = f"https://www.google.com/maps/search/{query}"
                
                tooltip_html = f"""
                <div style="font-family: sans-serif; width: 200px; padding: 5px;">
                    <h4 style="margin:0 0 10px 0;">{row['상호']}</h4>
                    <a href="{google_map_url}" target="_blank" 
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
            st.warning("이 지역에는 표시할 식당 데이터가 없습니다.")
else:
    st.warning("데이터 로드에 실패했습니다. 파일 이름과 컬럼명을 확인해 주세요.")

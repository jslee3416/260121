import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os
import urllib.parse

st.set_page_config(page_title="서울 맛집 구글맵 연동", layout="wide")

@st.cache_data
def load_data(file_name):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 인코딩 처리
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        # 컬럼 매칭 (상호, 구, 동, 위도, 경도 필수)
        cols = df.columns.tolist()
        name_variants = {
            '상호': ['상호명', '상호', 'POST_SJ', 'FACILITY_NM'],
            '구': ['자치구명', '구', 'SIGUNGU_NM', 'ADDR_NM'],
            '동': ['법정동명', '동', 'DONG_NM'],
            '위도': ['위도', '좌표_Y', 'LAT'],
            '경도': ['경도', '좌표_X', 'LOT']
        }
        
        actual_map = {}
        for key, variants in name_variants.items():
            match = next((c for c in cols if c in variants), None)
            if match: actual_map[match] = key
        
        df = df[list(actual_map.keys())].rename(columns=actual_map)
        df = df.dropna(subset=['위도', '경도']).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

DATA_FILE = "서울관광재단_식당운영정보_20230111.csv"
df = load_data(DATA_FILE)

if not df.empty:
    st.sidebar.title("📍 지역 선택")
    selected_gu = st.sidebar.selectbox("구 선택", sorted(df['구'].unique()))
    selected_dong = st.sidebar.selectbox("동 선택", sorted(df[df['구'] == selected_gu]['동'].unique()))
    
    filtered_df = df[(df['구'] == selected_gu) & (df['동'] == selected_dong)]
    
    # 페이지네이션
    rows_per_page = 20
    total_pages = max(len(filtered_df) // rows_per_page + 1, 1)
    current_page = st.sidebar.number_input(f"페이지 (1-{total_pages})", 1, total_pages, 1)
    page_df = filtered_df.iloc[(current_page-1)*rows_per_page : current_page*rows_per_page]

    st.title(f"🍴 {selected_gu} {selected_dong} 식당 목록")
    st.caption("식당 이름을 클릭하면 구글 맵 실시간 평점을 확인할 수 있습니다.")

    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        # 구글 검색 링크가 포함된 데이터프레임 생성
        display_df = page_df[['상호']].copy()
        display_df['구글검색'] = display_df['상호'].apply(lambda x: f"https://www.google.com/maps/search/{urllib.parse.quote(selected_gu + ' ' + x)}")
        st.write(f"현재 지역 식당: {len(filtered_df)}개")
        st.dataframe(display_df, use_container_width=True, height=500)

    with col2:
        if not page_df.empty:
            m = folium.Map(location=[page_df['위도'].mean(), page_df['경도'].mean()], zoom_start=15)
            cluster = MarkerCluster().add_to(m)
            
            for _, row in page_df.iterrows():
                # 구글 맵 검색 링크 생성
                search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(selected_gu + ' ' + row['상호'])}"
                
                tooltip_html = f"""
                <div style="font-family: sans-serif; width: 200px; padding: 5px;">
                    <h4 style="margin:0;">{row['상호']}</h4>
                    <p style="font-size:12px; color:gray;">서울관광재단 인증 식당</p>
                    <a href="{search_url}" target="_blank" style="display:inline-block; background:#4285F4; color:white; padding:5px 10px; border-radius:3px; text-decoration:none; font-size:12px;">
                        구글맵에서 평점 확인하기 ↗
                    </a>
                </div>
                """
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    tooltip=folium.Tooltip(tooltip_html, sticky=False),
                    icon=folium.Icon(color='red', icon='search', prefix='fa')
                ).add_to(cluster)
            
            st_folium(m, width="100%", height=500, key=f"map_{current_page}")
else:
    st.error("데이터를 불러올 수 없습니다.")

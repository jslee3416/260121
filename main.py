import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. 페이지 레이아웃 및 제목 설정
st.set_page_config(page_title="서울 맛집 가이드 2023", layout="wide")

# [최적화] 데이터 로드 및 전처리
@st.cache_data
def load_and_fix_data(file_name):
    try:
        # 파일 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_name)
        
        # 인코딩 처리 (공공데이터 표준인 CP949 먼저 시도)
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        # 컬럼명 유연 매칭 (서울관광재단 데이터의 실제 컬럼명 대응)
        cols = df.columns.tolist()
        name_variants = {
            '상호': ['상호명', '상호', 'POST_SJ', '업소명', 'FACILITY_NM'],
            '구': ['자치구명', '구', 'SIGUNGU_NM', 'ADDR_NM', '주소'],
            '동': ['법정동명', '동', 'DONG_NM', '행정동'],
            '위도': ['위도', '좌표_Y', 'LAT', 'Y_COORD', 'LATITUDE'],
            '경도': ['경도', '좌표_X', 'LOT', 'X_COORD', 'LON', 'LONGITUDE'],
            '평점': ['평점', 'RATING', 'STRP_RATING', 'STAR_POINT'],
            '전화': ['전화번호', 'TEL_NO', '전화', 'CONTACT']
        }
        
        actual_map = {}
        for key, variants in name_variants.items():
            match = next((c for c in cols if c in variants), None)
            if match:
                actual_map[match] = key
        
        # 매칭된 컬럼만 추출하여 이름 변경
        df = df[list(actual_map.keys())].rename(columns=actual_map)
        
        # 평점 숫자 변환 및 4.0 미만 즉시 삭제 (부하 최소화)
        df['평점'] = pd.to_numeric(df['평점'], errors='coerce').fillna(0)
        df = df[df['평점'] >= 4.0].reset_index(drop=True)
        
        # 좌표 숫자 변환 및 결측치 제거
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

# 제공해주신 정확한 파일명으로 호출
DATA_FILE = "서울관광재단_식당운영정보_20230111.csv"
df = load_and_fix_data(DATA_FILE)

# 2. 메인 서비스 로직
if not df.empty:
    st.sidebar.title("📍 지역 필터")
    
    # 구/동 선택
    gu_list = sorted(df['구'].unique())
    selected_gu = st.sidebar.selectbox("자치구 선택", gu_list)
    
    dong_list = sorted(df[df['구'] == selected_gu]['동'].unique())
    selected_dong = st.sidebar.selectbox("법정동 선택", dong_list)
    
    # 필터링 및 평점순 정렬
    filtered_df = df[(df['구'] == selected_gu) & (df['동'] == selected_dong)]
    filtered_df = filtered_df.sort_values(by='평점', ascending=False)
    
    st.title(f"🍴 {selected_gu} {selected_dong} 맛집")
    st.info(f"선택하신 지역에서 평점 4.0점 이상 식당 {len(filtered_df)}곳을 찾았습니다.")
    
    # 페이지네이션 (20개씩)
    rows_per_page = 20
    total_pages = max((len(filtered_df) // rows_per_page) + (1 if len(filtered_df) % rows_per_page > 0 else 0), 1)
    current_page = st.sidebar.number_input(f"페이지 (1-{total_pages})", 1, total_pages, 1)
    
    page_df = filtered_df.iloc[(current_page-1)*rows_per_page : current_page*rows_per_page]

    # 화면 분할
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader(f"📋 맛집 목록 ({current_page}P)")
        st.dataframe(page_df[['상호', '평점', '전화']], use_container_width=True, height=500)
        
    with col2:
        st.subheader("📍 지도 (마커에 커서를 올리세요)")
        if not page_df.empty:
            m = folium.Map(location=[page_df['위도'].mean(), page_df['경도'].mean()], zoom_start=15)
            cluster = MarkerCluster().add_to(m)
            
            for _, row in page_df.iterrows():
                # 툴팁: 커서 도달 시 표시, 이동 시 사라짐
                tooltip_html = f"""
                <div style="font-family: sans-serif; width: 180px;">
                    <h5 style='margin:0; color:#2c3e50;'>{row['상호']}</h5>
                    <div style='margin-top:5px; font-size:13px;'>
                        <b>⭐ 평점:</b> {row['평점']}<br>
                        <b>📞 전화:</b> {row['전화']}
                    </div>
                </div>
                """
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    tooltip=folium.Tooltip(tooltip_html, sticky=False),
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(cluster)
            
            st_folium(m, width="100%", height=500, key=f"map_{current_page}")
else:
    st.error(f"'{DATA_FILE}' 파일을 찾을 수 없거나 데이터가 비어있습니다.")
    st.info("GitHub 저장소에 파일이 정확한 이름으로 업로드되어 있는지 확인해주세요.")

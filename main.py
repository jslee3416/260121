import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# 1. 페이지 레이아웃 설정
st.set_page_config(
    page_title="서울시 맛집 추천 시스템",
    page_icon="🍴",
    layout="wide"
)

# [최적화 1] 데이터 로드 및 전처리 캐싱
@st.cache_data
def load_data(file_path):
    # 필요한 컬럼만 지정 (메모리 절약)
    # 실제 파일의 컬럼명에 맞춰 '상호명', '위도' 등을 수정하세요.
    use_cols = ['상호명', '자치구명', '법정동명', '위도', '경도', '전화번호', '평점']
    
    try:
        # 데이터 읽기
        df = pd.read_csv(file_path, usecols=use_cols)
        
        # [최적화 2] 평점 4점 미만 데이터는 읽어올 때 바로 삭제 (부하 감소)
        df = df[df['평점'] >= 4.0].reset_index(drop=True)
        
        # 위도/경도 결측치 제거
        df = df.dropna(subset=['위도', '경도'])
        
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 데이터 로드 (파일명 확인 필요)
df = load_data("seoul_restaurants.csv")

# 2. 사이드바 - 행정구역 선택 UI
st.sidebar.header("📍 지역 필터")

if not df.empty:
    # '구' 선택
    gu_list = sorted(df['자치구명'].unique())
    selected_gu = st.sidebar.selectbox("자치구(구)를 선택하세요", gu_list)

    # 선택된 '구'에 속한 '동' 목록만 추출
    dong_list = sorted(df[df['자치구명'] == selected_gu]['법정동명'].unique())
    selected_dong = st.sidebar.selectbox("법정동(동)을 선택하세요", dong_list)

    # 3. 데이터 필터링
    filtered_df = df[(df['자치구명'] == selected_gu) & (df['법정동명'] == selected_dong)]

    # 4. 메인 화면 출력
    st.title(f"🍴 {selected_gu} {selected_dong} 맛집 추천")
    st.markdown(f"평점 **4.0 이상**인 식당 **{len(filtered_df)}개**를 찾았습니다.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📋 식당 리스트")
        # 데이터프레임 표시 (불필요한 인덱스 제외)
        st.dataframe(
            filtered_df[['상호명', '평점', '전화번호']].sort_values(by='평점', ascending=False),
            use_container_width=True,
            height=550
        )

    with col2:
        st.subheader("📍 지도 보기")
        if not filtered_df.empty:
            # 지도 초기화 (검색된 식당들의 중앙 좌표)
            center_lat = filtered_df['위도'].mean()
            center_lon = filtered_df['경도'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

            # [최적화 3] 마커 클러스터링 적용 (지도 렌더링 속도 향상)
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in filtered_df.iterrows():
                # 툴팁 HTML 구성 (커서 올리면 표시됨)
                tooltip_html = f"""
                <div style="font-family: 'Nanum Gothic', sans-serif; width: 180px;">
                    <h5 style='margin-bottom:5px;'>{row['상호명']}</h5>
                    <b>평점:</b> ⭐{row['평점']}<br>
                    <b>전화:</b> {row['전화번호']}
                </div>
                """
                
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    tooltip=folium.Tooltip(tooltip_html),
                    icon=folium.Icon(color='blue', icon='restaurant', prefix='fa')
                ).add_to(marker_cluster)

            # 지도 표시
            st_folium(m, width="100%", height=550, returned_objects=[])
        else:
            st.info("해당 지역에 조건에 맞는 식당이 없습니다.")
else:
    st.warning("데이터 파일이 없거나 형식이 잘못되었습니다.")

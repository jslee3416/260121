import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# 1. 페이지 설정 (최상단 배치)
st.set_page_config(page_title="서울 맛집 지도", layout="wide")

# [조치 1] 데이터 캐싱: 한 번 로드한 데이터는 메모리에 저장하여 재실행 시 로딩 생략
@st.cache_data
def load_and_optimize_data(file_path):
    # [조치 2] 필요한 열(Column)만 선택적으로 로드하여 메모리 점유율 감소
    use_cols = ['상호명', '자치구명', '법정동명', '위도', '경도', '전화번호', '평점']
    
    # 실제 환경에서는 'your_data.csv' 파일 경로를 입력하세요.
    # 여기서는 예시를 위해 read_csv 구조만 작성합니다.
    try:
        df = pd.read_csv(file_path, usecols=use_cols)
    except:
        # 파일이 없을 경우를 대비한 샘플 데이터 생성 (테스트용)
        data = {
            '상호명': ['맛집A', '맛집B', '맛집C', '맛집D'],
            '자치구명': ['중구', '중구', '강남구', '강남구'],
            '법정동명': ['명동', '명동', '역삼동', '역삼동'],
            '위도': [37.561, 37.562, 37.498, 37.499],
            '경도': [126.985, 126.986, 127.027, 127.028],
            '전화번호': ['02-1', '02-2', '02-3', '02-4'],
            '평점': [4.5, 3.2, 4.8, 3.5]
        }
        df = pd.DataFrame(data)

    # [조치 3] 평점 4.0 미만 데이터 즉시 삭제 (데이터 부하 원천 차단)
    df = df[df['평점'] >= 4.0].reset_index(drop=True)
    
    return df

# 데이터 로드 (파일명을 실제 본인의 파일명으로 수정하세요)
df = load_and_optimize_data("seoul_restaurants.csv")

# 2. 사이드바 인터페이스
st.sidebar.title("📍 지역 및 필터")
gu_list = sorted(df['자치구명'].unique())
selected_gu = st.sidebar.selectbox("구 선택", gu_list)

dong_list = sorted(df[df['자치구명'] == selected_gu]['법정동명'].unique())
selected_dong = st.sidebar.selectbox("동 선택", dong_list)

# 3. 데이터 필터링
filtered_df = df[(df['자치구명'] == selected_gu) & (df['법정동명'] == selected_dong)]

# 4. 메인 화면 구성
st.title(f"⭐ {selected_gu} {selected_dong} 4점 이상 맛집")

col1, col2 = st.columns([1, 2])

with col1:
    st.write(f"검색 결과: {len(filtered_df)}곳")
    st.dataframe(filtered_df[['상호명', '평점', '전화번호']], use_container_width=True)

with col2:
    if not filtered_df.empty:
        # 지도 중심 설정
        m = folium.Map(location=[filtered_df['위도'].mean(), filtered_df['경도'].mean()], zoom_start=15)
        
        # [추가 조치] 마커 클러스터링: 마커가 많을 경우 그룹화하여 렌더링 부하 방지
        marker_cluster = MarkerCluster().add_to(m)
        
        for _, row in filtered_df.iterrows():
            tooltip_text = f"<b>{row['상호명']}</b><br>평점: ⭐{row['평점']}<br>전화: {row['전화번호']}"
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                tooltip=tooltip_text, # 마우스 호버 시 표시
                icon=folium.Icon(color='blue', icon='utensils', prefix='fa')
            ).add_to(marker_cluster)
        
        st_folium(m, width="100%", height=600)
    else:
        st.info("해당 지역에 평점 4점 이상의 식당이 없습니다.")

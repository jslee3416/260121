import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. 페이지 설정
st.set_page_config(layout="wide")
st.title("서울시 행정구역별 식당 추천 서비스 🍴")

# 2. 샘플 데이터 생성 (실제 환경에서는 API 또는 CSV 로드)
@st.cache_data
def load_data():
    # 실제로는 pd.read_csv() 또는 API 호출 코드가 들어갑니다.
    data = {
        '상호': ['무교동 낙지', '광화문 국밥', '명동 칼국수', '강남 수제버거', '신사 파스타'],
        '자치구명': ['중구', '중구', '중구', '강남구', '강남구'],
        '법정동명': ['무교동', '정동', '명동', '역삼동', '신사동'],
        'lat': [37.5670, 37.5685, 37.5600, 37.4980, 37.5240],
        'lon': [126.9790, 126.9770, 126.9850, 127.0270, 127.0220],
        '전화번호': ['02-111-1111', '02-222-2222', '02-333-3333', '02-444-4444', '02-555-5555'],
        '평점': [4.5, 4.2, 4.8, 3.9, 4.3]
    }
    return pd.DataFrame(data)

df = load_data()

# 3. 사이드바 - 행정구역 선택창
st.sidebar.header("📍 지역 선택")

# '구' 선택
sido_list = sorted(df['자치구명'].unique())
selected_gu = st.sidebar.selectbox("자치구(구)를 선택하세요", sido_list)

# 선택된 '구'에 해당하는 '동' 목록 필터링
dong_list = sorted(df[df['자치구명'] == selected_gu]['법정동명'].unique())
selected_dong = st.sidebar.selectbox("법정동(동)을 선택하세요", dong_list)

# 최소 평점 설정
min_rating = st.sidebar.slider("최소 평점 선택", 0.0, 5.0, 4.0, 0.1)

# 4. 데이터 필터링
filtered_df = df[
    (df['자치구명'] == selected_gu) & 
    (df['법정동명'] == selected_dong) & 
    (df['평점'] >= min_rating)
]

# 5. 결과 화면 구성
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"✅ {selected_gu} {selected_dong} 결과")
    st.write(f"총 {len(filtered_df)}개의 식당이 검색되었습니다.")
    st.dataframe(filtered_df[['상호', '평점', '전화번호']])

with col2:
    if not filtered_df.empty:
        # 필터링된 데이터의 중심점으로 지도 시작
        center = [filtered_df['lat'].mean(), filtered_df['lon'].mean()]
        m = folium.Map(location=center, zoom_start=15)

        for _, row in filtered_df.iterrows():
            tooltip_html = f"""
            <div style="width:200px">
                <h4>{row['상호']}</h4>
                <b>평점:</b> ⭐{row['평점']}<br>
                <b>전화:</b> {row['전화번호']}
            </div>
            """
            folium.Marker(
                location=[row['lat'], row['lon']],
                tooltip=folium.Tooltip(tooltip_html),
                icon=folium.Icon(color='blue', icon='restaurant', prefix='fa')
            ).add_to(m)
        
        # 지도 표시
        st_folium(m, width=800, height=500)
    else:
        st.warning("선택한 조건에 맞는 식당이 없습니다.")

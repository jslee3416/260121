import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster


# 기존 코드 수정
@st.cache_data
def load_optimized_data(file_path):
    try:
        use_cols = ['상호명', '자치구명', '법정동명', '위도', '경도', '전화번호', '평점']
        
        # [수정된 부분] encoding='cp949'를 추가하여 한글 깨짐 방지
        try:
            df = pd.read_csv(file_path, usecols=use_cols, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, usecols=use_cols, encoding='cp949') # 엑셀 한글 표준
            
        df = df[df['평점'] >= 4.0].reset_index(drop=True)
        df = df.dropna(subset=['위도', '경도'])
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()














# 1. 페이지 설정


# 데이터 로드 (파일명 확인 필요)
df = load_optimized_data("서울관광재단_식당운영정보_20230111.csv")

# 2. 사이드바 - 지역 선택
st.sidebar.header("📍 지역 필터")
if not df.empty:
    gu_list = sorted(df['자치구명'].unique())
    selected_gu = st.sidebar.selectbox("구 선택", gu_list)

    dong_list = sorted(df[df['자치구명'] == selected_gu]['법정동명'].unique())
    selected_dong = st.sidebar.selectbox("동 선택", dong_list)

    # 선택 지역 데이터 필터링
    filtered_df = df[(df['자치구명'] == selected_gu) & (df['법정동명'] == selected_dong)]
    filtered_df = filtered_df.sort_values(by='평점', ascending=False) # 평점순 정렬

    # 3. [핵심 기능] 페이지네이션 (20개씩 보여주기)
    st.sidebar.markdown("---")
    st.sidebar.write(f"총 검색 결과: {len(filtered_df)}개")
    
    rows_per_page = 20
    total_pages = (len(filtered_df) // rows_per_page) + (1 if len(filtered_df) % rows_per_page > 0 else 0)
    
    if total_pages > 0:
        current_page = st.sidebar.number_input(f"페이지 (총 {total_pages}P)", min_value=1, max_value=total_pages, step=1)
        
        # 현재 페이지에 해당하는 데이터만 추출
        start_idx = (current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        page_df = filtered_df.iloc[start_idx:end_idx]
    else:
        page_df = pd.DataFrame()

    # 4. 메인 화면 구성
    st.title(f"🍴 {selected_gu} {selected_dong} 맛집 (페이지 {current_page}/{total_pages})")

    if not page_df.empty:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader(f"📋 리스트 ({start_idx+1}~{min(end_idx, len(filtered_df))}위)")
            st.dataframe(
                page_df[['상호명', '평점', '전화번호']],
                use_container_width=True,
                height=500
            )

        with col2:
            st.subheader("📍 지도 표시")
            # 지도 중심점 설정
            m = folium.Map(location=[page_df['위도'].mean(), page_df['경도'].mean()], zoom_start=15)
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in page_df.iterrows():
                tooltip_html = f"""
                <div style="width:180px;">
                    <b>{row['상호명']}</b><br>
                    평점: ⭐{row['평점']}<br>
                    전화: {row['전화번호']}
                </div>
                """
                folium.Marker(
                    location=[row['위도'], row['경도']],
                    tooltip=folium.Tooltip(tooltip_html),
                    icon=folium.Icon(color='blue', icon='restaurant', prefix='fa')
                ).add_to(marker_cluster)

            st_folium(m, width="100%", height=500, key=f"map_{current_page}")
    else:
        st.info("선택한 지역에 평점 4점 이상의 식당이 없습니다.")
else:
    st.warning("데이터 파일을 찾을 수 없습니다.")

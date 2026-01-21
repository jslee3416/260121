import streamlit as st
import requests
import pandas as pd
import googlemaps
import folium
from streamlit_folium import folium_static
from math import radians, cos, sin, asin, sqrt

import streamlit as st

st.set_page_config(page_title="서울 맛집 가이드", layout="wide", page_icon="🍴")

st.title("🍴 서울시 고평점 식당 추천 서비스")
st.markdown("---")
st.subheader("이 앱은 다음과 같은 기능을 제공합니다:")
st.write("1. **공공데이터 활용**: 서울관광재단의 신뢰할 수 있는 식당 정보를 불러옵니다.")
st.write("2. **실시간 평점**: Google Maps API를 통해 현재 실제 고객 평점을 확인합니다.")
st.write("3. **거리 및 평점 필터**: 내 주변 1km 이내, 3~5점 사이의 맛집만 골라냅니다.")

st.info("👈 왼쪽 사이드바의 '추천 지도' 메뉴를 클릭하여 시작하세요!")

# --- 1. API 키 및 설정 ---
# 실제 발급받은 키로 교체하세요
SEOUL_DATA_KEY = 'YOUR_PUBLIC_DATA_PORTAL_KEY'
GOOGLE_MAPS_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)

# 거리 계산 함수
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    c = 2 * asin(sqrt(sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2))
    return c * 6371

@st.cache_data
def get_seoul_data():
    """서울관광재단 API 호출"""
    url = f"http://apis.data.go.kr/B551011/KorService1/areaBasedList1"
    params = {
        'serviceKey': SEOUL_DATA_KEY,
        'numOfRows': '50', # 테스트를 위해 50개로 제한
        'areaCode': '1',
        'contentTypeId': '39',
        'MobileOS': 'ETC',
        'MobileApp': 'App',
        '_type': 'json'
    }
    try:
        res = requests.get(url, params=params)
        return pd.DataFrame(res.json()['response']['body']['items']['item'])
    except:
        return pd.DataFrame()

# --- 2. UI 레이아웃 ---
st.title("📍 내 주변 맛집 필터링")

# 사이드바 설정
st.sidebar.header("🔍 검색 필터")
target_rating = st.sidebar.slider("최소 구글 평점 (0.5 단위)", 3.0, 5.0, 4.0, step=0.5)
radius_km = st.sidebar.select_slider("검색 반경 (km)", options=[0.5, 1.0, 1.5, 2.0], value=1.0)

# 기준 좌표 (서울시청)
my_lat, my_lng = 37.5665, 126.9780

if st.button(f"반경 {radius_km}km 내 맛집 찾기"):
    with st.spinner("공공데이터와 구글 평점을 분석 중..."):
        df = get_seoul_data()
        
        if df.empty:
            st.error("데이터를 불러오지 못했습니다. API 키를 확인하세요.")
        else:
            results = []
            for _, row in df.iterrows():
                r_lat, r_lng = float(row['mapy']), float(row['mapx'])
                dist = haversine(my_lng, my_lat, r_lng, r_lat)
                
                if dist <= radius_km:
                    # 구글 평점 검색
                    place_res = gmaps.places(query=row['title'])
                    if place_res['results']:
                        p = place_res['results'][0]
                        rating = p.get('rating', 0)
                        
                        if rating >= target_rating:
                            results.append({
                                '상호명': row['title'],
                                '평점': rating,
                                '위치': [r_lat, r_lng],
                                '주소': p.get('vicinity', row.get('addr1', ''))
                            })

            if results:
                st.success(f"{len(results)}개의 맛집을 찾았습니다!")
                
                # 지도 표시
                m = folium.Map(location=[my_lat, my_lng], zoom_start=15)
                folium.Marker([my_lat, my_lng], tooltip="내 위치", icon=folium.Icon(color='red')).add_to(m)
                
                for item in results:
                    # 마커 및 툴팁(호버 시 상호명/평점) 설정
                    folium.Marker(
                        location=item['위치'],
                        tooltip=f"<b>{item['상호명']}</b><br>평점: ⭐{item['평점']}",
                        popup=item['주소'],
                        icon=folium.Icon(color='blue', icon='cutlery', prefix='fa')
                    ).add_to(m)
                
                folium_static(m)
                
                # 테이블 표시
                st.table(pd.DataFrame(results)[['상호명', '평점', '주소']])
            else:
                st.warning("조건에 맞는 식당이 없습니다. 필터를 조정해 보세요.")

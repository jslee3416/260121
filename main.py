import streamlit as st
import requests
import pandas as pd
import googlemaps
import folium
from streamlit_folium import folium_static
from math import radians, cos, sin, asin, sqrt

# --- 설정 및 API 키 (이전과 동일) ---
SEOUL_DATA_KEY = 'YOUR_PUBLIC_DATA_PORTAL_KEY'
GOOGLE_MAPS_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'
gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)

st.set_page_config(page_title="서울 맛집 지도", layout="wide")
st.title("📍 서울관광재단 데이터 기반 고평점 식당 찾기")

# --- 유틸리티 함수 (Haversine 등 이전 코드와 동일) ---
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

@st.cache_data
def get_seoul_tour_data():
    # 실제 연동 시 API 엔드포인트와 파라미터를 입력하세요.
    # 여기서는 구조 예시를 보여줍니다.
    url = f"http://apis.data.go.kr/B551011/KorService1/areaBasedList1"
    params = {
        'serviceKey': SEOUL_DATA_KEY,
        'numOfRows': '100',
        'pageNo': '1',
        'MobileOS': 'ETC',
        'MobileApp': 'AppTest',
        '_type': 'json',
        'areaCode': '1',
        'contentTypeId': '39'
    }
    try:
        res = requests.get(url, params=params)
        items = res.json()['response']['body']['items']['item']
        return pd.DataFrame(items)
    except:
        # 샘플 데이터 (테스트용)
        return pd.DataFrame([
            {'title': '서울시청 근처 맛집', 'mapx': '126.9785', 'mapy': '37.5668', 'addr1': '서울 중구'},
            {'title': '덕수궁 식당', 'mapx': '126.9750', 'mapy': '37.5658', 'addr1': '서울 중구'}
        ])

def get_google_info(place_name):
    """구글에서 평점과 상세 정보 가져오기"""
    places = gmaps.places(query=place_name)
    if places['results']:
        place = places['results'][0]
        return place.get('rating', 0), place.get('vicinity', '주소 정보 없음')
    return 0, ""

# --- 사이드바 설정 (추가 요청 반영) ---
st.sidebar.header("🔍 상세 필터")

# 1. 평점 선택 (3.0 ~ 5.0 사이, 0.5 단위)
# 사용자가 범위를 선택하게 하거나 특정 점수 이상을 선택하게 할 수 있습니다.
selected_rating = st.sidebar.slider(
    "최소 구글 평점 선택",
    min_value=3.0, 
    max_value=5.0, 
    value=4.0,     # 기본값 4.0
    step=0.5       # 0.5 단위 조절
)

# 2. 검색 거리 설정
dist_range = st.sidebar.selectbox("검색 반경", [0.5, 1.0, 1.5, 2.0], index=1) # 기본 1.0km

# --- 메인 실행 ---
my_lat, my_lng = 37.5665, 126.9780 # 기준: 서울시청

if st.button(f'반경 {dist_range}km 내 평점 {selected_rating} 이상 식당 찾기'):
    with st.spinner('공공데이터와 구글 평점을 분석 중입니다...'):
        df_tour = get_seoul_tour_data()
        results = []

        for _, row in df_tour.iterrows():
            res_lat, res_lng = float(row['mapy']), float(row['mapx'])
            dist = haversine(my_lng, my_lat, res_lng, res_lat)
            
            if dist <= dist_range:
                rating, g_addr = get_google_info(row['title'])
                
                # 사용자가 설정한 평점 이상인 경우만 추가
                if rating >= selected_rating:
                    results.append({
                        'name': row['title'],
                        'lat': res_lat,
                        'lng': res_lng,
                        'rating': rating,
                        'address': g_addr if g_addr else row.get('addr1', '')
                    })

        if results:
            # 지도 생성
            m = folium.Map(location=[my_lat, my_lng], zoom_start=15)
            folium.Marker([my_lat, my_lng], tooltip="내 위치 (서울시청)", icon=folium.Icon(color='red')).add_to(m)

            for item in results:
                # 툴팁 (마우스 호버 시 상호명/평점 표시)
                tooltip_content = f"<b>{item['name']}</b><br>평점: ⭐{item['rating']}"
                
                folium.Marker(
                    [item['lat'], item['lng']],
                    tooltip=tooltip_content,
                    popup=item['address'],
                    icon=folium.Icon(color='blue', icon='cutlery', prefix='fa')
                ).add_to(m)

            folium_static(m)
            st.success(f"조건에 맞는 식당 {len(results)}곳을 찾았습니다.")
        else:
            st.error("조건에 맞는 식당이 근처에 없습니다. 필터를 변경해 보세요.")

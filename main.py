
import folium
import pandas as pd
import requests
from math import radians, cos, sin, asin, sqrt

# 1. 하버사인 공식 (두 지점 사이의 거리 계산)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반지름 (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 1000  # 미터 단위 변환

# 2. 현재 내 위치 설정 (예: 서울시청)
# 실제 웹앱에서는 브라우저 GPS 값을 가져오거나 input을 받도록 구성할 수 있습니다.
my_location = [37.5665, 126.9780] 

# 3. 데이터 불러오기 (서울관광재단 데이터 예시 구조)
# 여기서는 예시를 위해 데이터프레임을 직접 생성하지만, 
# 실제로는 requests.get(API_URL)을 통해 받아온 JSON/CSV를 사용합니다.
data = {
    '상호': ['무교동 낙지', '광화문 국밥', '정동 칼국수', '덕수궁 와플', '시청 소바'],
    'lat': [37.5670, 37.5685, 37.5645, 37.5658, 37.5690],
    'lon': [126.9790, 126.9770, 126.9750, 126.9765, 126.9805],
    '전화번호': ['02-123-4567', '02-234-5678', '02-345-6789', '02-456-7890', '02-567-8901'],
    '평점': [4.5, 4.2, 3.8, 4.8, 4.1]
}
df = pd.DataFrame(data)

# 4. 지도 생성 및 반경 표시
m = folium.Map(location=my_location, zoom_start=16)

# 내 위치 표시
folium.Marker(my_location, icon=folium.Icon(color='red', icon='info-sign'), tooltip="내 위치").add_to(m)

# 반경 서클 표시 (300m, 500m, 1000m)
for radius, color in zip([300, 500, 1000], ['blue', 'green', 'orange']):
    folium.Circle(
        location=my_location,
        radius=radius,
        color=color,
        fill=True,
        fill_opacity=0.1,
        tooltip=f'반경 {radius}m'
    ).add_to(m)

# 5. 거리 계산 및 조건 필터링 (평점 4점 이상, 반경 내 식당)
for idx, row in df.iterrows():
    dist = haversine(my_location[0], my_location[1], row['lat'], row['lon'])
    
    # 반경 1000m 이내이고 평점이 4.0 이상인 경우만 마커 표시
    if dist <= 1000 and row['평점'] >= 4.0:
        # 마우스 호버 시 나타날 툴팁 구성
        tooltip_html = f"""
        <div style="font-family: sans-serif;">
            <h4>{row['상호']}</h4>
            <b>전화:</b> {row['전화번호']}<br>
            <b>평점:</b> ⭐{row['평점']}
        </div>
        """
        
        folium.Marker(
            location=[row['lat'], row['lon']],
            tooltip=folium.Tooltip(tooltip_html, sticky=False), # 커서 이동 시 사라짐
            icon=folium.Icon(color='cadetblue', icon='cutlery', prefix='fa')
        ).add_to(m)

# 6. 결과 저장 및 확인
m.save('restaurant_map.html')
print("지도가 'restaurant_map.html'로 저장되었습니다.")

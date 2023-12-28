# **************************************************************************************************************
# Date: Jan 31, 2023
# update on Jan 31, 2023
# Author: Kyusang Kwon
# Description: To calculate EMS accessbility
# Virtual environment: access with python 3.10.9
# **************************************************************************************************************

# 분석단계
# 1. 데이터 불러오기
#    - 격자별 인구수
#    - 소방서 위치 및 응급의료센터 위치
#    - 교통네트워크
# 2. 링크별 시간 구하기: R에서 작업(sfnetwork)
# 3. 접근성 구하기

# 데이터 불러오기
# 인구데이터
# 격자

# 가상환경 라이브러리 불러오기
import sys
import os
import pandas as pd
import numpy as np
import geopandas as gpd

from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import folium
import webbrowser

# 자체 생성 모듈 불러오기
sys.path.append("D:\Analysis\Postgres")
sys.path.append("D:\Analysis\EMS_access")
sys.path.append("D:\Analysis\mapping")
import postgres as pg # postgreSQL 관련 함수들
import G2SFCA # 접근성 분석 함수들
import gdf_folium

# 작업환경 설정
os.chdir("D:\Analysis\EMS_access")


### 분석
# 1. 분석데이터 불러오기
# 1) 수요
query = "SELECT a.\"GRID_500M_\" as grdcode, a.geometry as geom, b.pop as pop \
        FROM sp.\"grd500M_sgis_2022\" as a \
        LEFT JOIN (SELECT * FROM nsp.grd500m_sgispop_2021 WHERE statcode = 'to_in_001') as b \
        ON a.\"GRID_500M_\" = b.grdcode;"
demand = pg.getSpatialData(query = query, geometry_col = 'geom')

query = "SELECT * FROM sp.sd_sgis_2022_2q WHERE sido_cd = '33';"
basemap = pg.getSpatialData(query = query, geometry_col = 'geom')


# 집계구
query = "SELECT a.tot_reg_cd as tot_reg_cd, b.value as pop, a.geom as geom\
        FROM sp.tot_sgis_2021_4q as a\
        LEFT JOIN  (SELECT tot_reg_cd, value FROM nsp.tot_sgisPop_2021 WHERE statcode = 'to_in_001') as b\
        ON a.tot_reg_cd = b.tot_reg_cd WHERE a.tot_reg_cd LIKE '33%%';" # python에서 SQL의 LIKE문을 쓸 경우 %는 %%로 사용
tot = pg.getSpatialData(query = query, geometry_col = 'geom')
tot_ctrd = gpd.GeoDataFrame({'tot_reg_cd':tot['tot_reg_cd'], 'pop': tot['pop'], 'geom':tot['geom'].centroid}, 
                            geometry = 'geom', 
                            crs="EPSG:5179")

# 공급
# 1) 소방서
query = "SELECT center_nm, x, y FROM nsp.ind_119center_2021 WHERE sido_hq = '충북';" # python에서 SQL의 LIKE문을 쓸 경우 %는 %%로 사용
firestation_df = pg.getData(query = query)
firestation = gpd.GeoDataFrame(firestation_df['center_nm'], 
                               geometry = gpd.points_from_xy(firestation_df.x, firestation_df.y), 
                               crs = 5179)

# 2) 병원
query = "SELECT a.hp_code as hp_code, a.hp_nm as hp_nm, a.address as address, b.bed_8 as bed, a.lon as lon, a.lat as lat \
         FROM nsp.ind_hospital_202203 as a \
         LEFT JOIN ind_hospital_bedinfo_202203 as b \
           ON a.hp_code = b.hp_code \
         WHERE b.sd_nm = '충북' and b.bed_8 > 0;"
hospital_df = pg.getData(query = query)
hospital = gpd.GeoDataFrame(hospital_df[['hp_code', 'bed']],
                            geometry = gpd.points_from_xy(hospital_df.lon, hospital_df.lat), 
                            crs = 4326).to_crs(5179)                         

# 수요-공급 자료 export
tot_ctrd.to_file('clean_input/poptot_centroid.gpkg', layer='poptot_centroid', driver="GPKG")
firestation.to_file('clean_input/firestation.gpkg', layer='firestation', driver="GPKG")
hospital.to_file('clean_input/hospital.gpkg', layer='hospital', driver="GPKG")

# 수요-공급-교통 DataFrame 읽기(R 작업)
fs_to_tot = pd.read_csv("clean_input/fs_to_tot.txt", sep='\t', header=0, na_values = ['Inf'])
tot_to_ems = pd.read_csv("clean_input/tot_to_ems.txt", sep='\t', header=0)

# G2SFCA 실행
access1 = G2SFCA.Generalized2SFCA(data = fs_to_tot,
                        demand_id = 'd_id',
                        demand_col = 'pop',
                        supply_id = 'o_id',
                        supply_col = 1,
                        cost_id = 'cost',
                        catchment = 5,
                        impedance_beta = 5)

access2 = G2SFCA.Generalized2SFCA(data = tot_to_ems,
                        demand_id = 'o_id',
                        demand_col = 'pop',
                        supply_id = 'd_id',
                        supply_col = 'bed',
                        cost_id = 'cost',
                        catchment = 5,
                        impedance_beta = 5)


# 지도화: 수요-공급
fig, ax = plt.subplots(1,3)

tot.to_crs(4326).plot(column = 'pop', ax=ax[0], scheme ='naturalbreaks', k=4,
        cmap = 'OrRd',
        #figuresize = (15,15),
        legend=True,
        legend_kwds ={'loc':'center right', 'bbox_to_anchor': (1,0.2)})\
    .set_title("Population Distribution by Census Track")

tot.to_crs(4326).plot(ax = ax[1], color = 'white', edgecolor='lightgray')
hospital.to_crs(4326).plot(ax = ax[1], marker = "*", color='red', markersize = 100)\
    .set_title("Spatial Distribution of EMS")

tot.to_crs(4326).plot(ax = ax[2], color = 'white', edgecolor='lightgray')
firestation.to_crs(4326).plot(ax = ax[2], marker = "o", color='blue', markersize = 100)\
    .set_title("Spatial Distribution of Firestation")
    
plt.show()

# scale 추가: geoDataFrame.plot().add_artist(ScaleBar(dx=1,units="km",location='lower left'))


## 지도화: 접근성
access_fs_to_tot = tot.to_crs(4326).merge(access1, how = 'left', left_on = 'tot_reg_cd', right_on = 'd_id')
access_tot_to_ems = tot.to_crs(4326).merge(access2, how = 'left', left_on = 'tot_reg_cd', right_on = 'o_id')
access_total = pd.concat([tot.to_crs(4326), access_fs_to_tot['accessibility']+access_tot_to_ems['accessibility']], axis = 1)

fig, ax = plt.subplots(1,3)

tot.to_crs(4326).plot(ax = ax[0], color = 'white', edgecolor='lightgray')
access_fs_to_tot.plot(column = 'accessibility', ax=ax[0], scheme ='quantiles', k=4,
        cmap = 'OrRd',
        #figuresize = (15,15),
        legend=True,
        legend_kwds ={'loc':'center right', 'bbox_to_anchor': (1,0.2)})\
    .set_title("Accessibility to firestation")

tot.to_crs(4326).plot(ax = ax[1], color = 'white', edgecolor='lightgray')
access_tot_to_ems.plot(column = 'accessibility', ax=ax[1], scheme ='quantiles', k=4,
        cmap = 'OrRd',
        #figuresize = (15,15),
        legend=True,
        legend_kwds ={'loc':'center right', 'bbox_to_anchor': (1,0.2)})\
    .set_title("Accessibility to EMS")

tot.to_crs(4326).plot(ax = ax[2], color = 'white', edgecolor='lightgray')
access_total.plot(column = 'accessibility', ax=ax[2], scheme ='quantiles', k=4,
        cmap = 'OrRd',
        #figuresize = (15,15),
        legend=True,
        legend_kwds ={'loc':'center right', 'bbox_to_anchor': (1,0.2)})\
    .set_title("Total Accessibility")

plt.show()

# 지도화: folium 활용
# basemap
m = folium.Map(location=[37.511877, 127.059505], tiles = 'CartoDB positron', zoom_start=8)

access_map = folium.Choropleth(
    geo_data = tot,
    name='Access',
    data= access1,
    columns=['d_id', 'accessibility'],
    key_on='feature.properties.tot_reg_cd',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.5,
    legend_name='accessibility to firestation')
access_map.add_to(m)
folium.features.GeoJsonPopup(fields = ['pop']).add_to(access_map.geojson)
access_map.geojson.add_to(m)
folium.LayerControl().add_to(m)
m.save("index.html")
webbrowser.open_new("index.html")





# 포인트 dataframe을 json으로 변환
firestation_4326 = firestation.to_crs(4326)

for _, r in firestation_4326.iterrows():
    folium.Marker(location = [r.geometry.xy[1][0], r.geometry.xy[0][0]],
                  popup = r['center_nm'],
                  icon = folium.Icon(color = 'blue', icon = 'star')).add_to(m)


m.save("index.html")
webbrowser.open_new("index.html")


## 
import matplotlib.colorbar
tot_wgs84 = tot.to_crs(4326)

m = tot.explore(
    column = 'pop',
    tooltip = 'tot_reg_cd',
    popup = True,
    tiles = 'CartoDB positron',
    scheme = 'naturalbreaks',
    k = 5,
    cmap = 'YlOrRd',
    style_kwds=dict(color="black")
)

m.save("index.html")
webbrowser.open_new("index.html")


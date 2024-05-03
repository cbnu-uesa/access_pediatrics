
# reference: https://cran.r-project.org/web/packages/sfnetworks/vignettes/sfn04_routing.html


library(sfnetworks)
library(sf)
library(tidyverse)
library(tidygraph)


setwd("D:\\Analysis\\EMS_access")

# read data
#origin <- 
#destination <-
roadNetwork_input <- read_sf("D:/05.Data/sp/road6_viewT_2019/road6_viewT_chungbuk_2019.shp")

orig = st_sfc(st_point(c(1025368.169, 1886087.496)), crs = 5179)
dest = st_sfc(st_point(c(1025902.357, 1885893.179)), crs = 5179)

st_transform(dest, 4326)

firestation = read_sf("D:/Analysis/EMS_access/clean_input/firestation.gpkg")
tot = read_sf("D:/Analysis/EMS_access/clean_input/poptot_centroid.gpkg")
hospital = read_sf("D:/Analysis/EMS_access/clean_input/hospital.gpkg")


# Calculate OD Cost Matrix
roadNetwork_input <- roadNetwork_input %>%
  mutate(max_speed = as.integer(max_speed)) %>%
  mutate(max_speed = ifelse(max_speed == 0, 50, max_speed)) # 제한속도 사용, 속도 없는 곳은 50km/h를 설정

duplicate <- roadNetwork_input %>%
  filter(oneway == "0") # 일방통행을 고려하기 위해 일방통행 아닌 링크만 복제
duplicate <- st_reverse(duplicate) # 일방통행 아닌 링크를 역방향으로 만듦(예. 노드 1->노드8로 연결되는 링크를 노드 8->노드 1로 수정)

roadNetwork_data <- rbind(roadNetwork_input, duplicate) # 원본과 일방통행 아닌 도로를 결합

roadNetwork_data <- as_sfnetwork(roadNetwork_data, direct = TRUE) %>% # direct =TRUE 옵션으로 방향이 있는 네트워크로 설정
    st_transform(5179) %>%
    activate("edges") %>%
    mutate(distance = edge_length()) %>%
    mutate(weight = units::drop_units((distance/1000)/(max_speed/3600)))


# calculate OD cost matrix with sfnetwork
CostToTot <- st_network_cost(roadNetwork_data, orig, dest, weights = "weight")
CostToTot <- st_network_cost(roadNetwork_data, firestation, tot, weights = "weight")
CostToEMS <- st_network_cost(roadNetwork_data, tot, hospital, weights = "weight")

costtable = data.frame(o_id="", d_id="", cost = 1)

ODCostMatrix = CostToEMS
origin = tot
destination = hospital

for(i in 1:nrow(ODCostMatrix)){
  for(j in 1:ncol(ODCostMatrix)){
    tmp = data.frame(o_id=origin$center_nm[i], d_id=destination$tot_reg_cd[j], cost=ODCostMatrix[i,j])
    costtable = rbind(costtable, tmp)
  }
}

for(i in 1:nrow(ODCostMatrix)){
  for(j in 1:ncol(ODCostMatrix)){
    tmp = data.frame(o_id=origin$tot_reg_cd[i], d_id=destination$hp_code[j], cost=ODCostMatrix[i,j])
    costtable = rbind(costtable, tmp)
  }
}



fs_to_tot = costtable[-1, ]
tot_to_ems = costtable[-1, ]

fs_to_tot_final = left_join(fs_to_tot, select(tot, tot_reg_cd, pop), by = c('d_id' = 'tot_reg_cd')) %>% select(-geom)
tot_to_ems_final = left_join(tot_to_ems, select(tot, tot_reg_cd, pop), by = c('o_id' = 'tot_reg_cd')) %>%
  select(-geom) %>%
  left_join(select(hospital, hp_code, bed), by = c('d_id' = 'hp_code')) %>%
  select(-geom)

write_delim(fs_to_tot_final, "clean_input/fs_to_tot.txt", delim='\t')
write_delim(tot_to_ems_final, "clean_input/tot_to_ems.txt", delim='\t')


tot_to_ems[, .(abc = 1)]


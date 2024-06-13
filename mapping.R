library(tidyverse)
library(sf)
library(tmap)
library(extrafont)


# Set working directory
path_wd <- dirname(rstudioapi::getSourceEditorContext()$path)
setwd(path_wd)

# load fonts: 한번만 실행
font_import()
loadfonts()

# load data
sejong <- read_sf("data/sejong_500m_grid.gpkg")
sejong_supply <- read_sf("data/new_sup_sf.gpkg")
access <- read_csv("output/g2sfca_30.csv")

sejong <- left_join(sejong, access, by = c("SPO_NO_CD" = "demand_id"))

## mapping
tm_shape(sejong) +
  tm_fill(col = "accessibility", style = "pretty", n = 5, 
          #breaks = c(-Inf, -0.5, -0.25, 0, 0.25, 0.5, Inf),
          legend.hist = FALSE, title = "Accessibility",
          palette = "viridis") +
  tm_layout(legend.outside = FALSE,
            legend.outside.position = "right",
            legend.title.size = 1.5,
            legend.title.fontfamily = "Arial",
            legend.title.fontface = "bold",
            legend.text.fontfamily = "Arial",
            legend.text.size = 1.1) +
  tm_compass(position = c("left", "bottom"), size = 4, show.labels = 0)+
  tm_scale_bar(position = c("left", "bottom"), size = 1, breaks = c(0, 2.5, 5)) +
  #tm_shape(seoul_gu)+
  tm_borders()

map <- tm_shape(sejong) +
  tm_fill(col = "spar", style = "fixed", n = 6, 
          breaks = c(-Inf, -0.5, -0.25, 0, 0.25, 0.5, Inf),
          legend.hist = FALSE, title = "Accessibility (SPAR)",
          palette = "-RdBu") +
  tm_layout(legend.outside = FALSE,
            legend.outside.position = "right",
            legend.title.size = 1.5,
            legend.title.fontfamily = "Arial",
            legend.title.fontface = "bold",
            legend.text.fontfamily = "Arial",
            legend.text.size = 1.1) +
  tm_compass(position = c("left", "bottom"), size = 4, show.labels = 0)+
  tm_scale_bar(position = c("left", "bottom"), width = 1, size = 1, breaks = c(0, 2.5, 5)) +
  tm_borders()

map <-  map + tm_shape(sejong_supply) +  # sejong_supply 포인트 데이터를 추가합니다
  tm_dots(size = 0.5, col = "blue", title = "Supply Points")  # 포인트 데이터를 시각화합니다

map

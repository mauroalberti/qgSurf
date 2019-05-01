library(foreign)
library(plotrix)

source_file <- "/home/mauro/Documents/Ricerca/Paperi/qgSurf_CalLuc/paper_review/gis_data/layers/Plane-point distances plane 072_39.dbf"
x <- read.dbf(source_file)

summary(x)

par(mfrow=c(1,1))

plot(x$src_geo_ds, 
     x$geo_prj_ds,
     main="Geographic point - plane distance", 
     xlab="Source point - geographic point distance", 
     ylab="Distance (meters)",
     pch=".",
     #xlim=c(0,5000),
     #ylim=c(-400, 200),
     col="red")
grid()


source_file <- "/home/mauro/Documents/Ricerca/Paperi/qgSurf_CalLuc/paper_review/gis_data/layers/Plane-point distances plane 082_40.dbf"
x <- read.dbf(source_file)

summary(x)

par(mfrow=c(1,1))

plot(x$src_geo_ds, 
     x$geo_prj_ds,
     main="Geographic point - plane distance", 
     xlab="Source point - geographic point distance", 
     ylab="Distance (meters)",
     pch=".",
     #xlim=c(0,5000),
     #ylim=c(-400, 200),
     col="red")
grid()
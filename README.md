[![Build Status](https://travis-ci.org/Porbi96/GFS-forecast-web-app.svg?branch=master)](https://travis-ci.org/Porbi96/GFS-forecast-web-app)
[![Coverage Status](https://coveralls.io/repos/github/Porbi96/GFS-forecast-web-app/badge.svg?branch=master)](https://coveralls.io/github/Porbi96/GFS-forecast-web-app?branch=master)

# Weather visualization App

This app makes weather maps based on NOAA's GFS numeric forecast.
By default, it shows these parameters for teritory of Poland(easily changeable):
- Temperature at 2m
- dew point
- 6h cumulated precipitation
- Pressure reduced to sea level
- Wind at 10m and 250hPa lvl (with vectors)
- Ground wind gust
- Surface based lifted index, convective available potential energy and convective inhibition

You can check the [demo here](https://gfs-vis.herokuapp.com/)
Due to server limitations, the data is being updated only occasionally.

## Requirements
* Python 3.7 or newer
* (Reccomended) Conda
* GDAL, Basemap, Dash and other packages included in `requirements.txt`

The full environment preparation can be based on `.travis.yml` file.

## Running
To start app:
1. Clone repo.
2. prepare all required libs and packages.
3. Run `project/web_app.py`.
4. To keep data up to date, run `project/raw_data_visualization.py` too and keep both scripts working.

## License
You can use the whole code as you want, as it's written in `LICENSE` file, but remember that used shapefiles are only for non-commercial use.
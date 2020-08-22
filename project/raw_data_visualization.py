import os
import re
import time

os.environ["PROJ_LIB"] = "C:\\Python\\Anaconda\\Library\\share"
import requests, gdal, csv
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from scipy.ndimage import convolve
from typing import List

DIRNAME = os.path.dirname(__file__) + "/.."

EXTENT_POLAND = [13, 25, 56, 48]

BANDS = {
    "Wind gust ground": 11,        # [m/s]
    "Wind 250hPa": [146, 147],
    # "u-component 250hPa": 146,     # [m/s]
    # "v-component 250hPa": 147,     # [m/s]
    "Temperature 2m": 415,         # ['C]
    "Dew point 2m": 417,           # ['C]
    "Wind 10m": [420, 421],
    # "u-component 10m": 420,        # [m/s]
    # "v-component 10m": 421,        # [m/s]
    # "Precipitation ground": 424,   # [kg/m^2 s]
    "LI surface": 432,             # ['C]
    "CAPE surface": 433,           # [J/kg]
    "CIN surface": 434,            # [J/kg]
    "Pressure sea lvl": 520        # [Pa]
}

BANDS_NONZERO = {
    "Wind gust ground": 11,  # [m/s]
    "Wind 250hPa": [149, 150],
    # "u-component 250hPa": 146,     # [m/s]
    # "v-component 250hPa": 147,     # [m/s]
    "Temperature 2m": 435,  # ['C]
    "Dew point 2m": 437,  # ['C]
    "Wind 10m": [442, 443],
    # "u-component 10m": 420,        # [m/s]
    # "v-component 10m": 421,        # [m/s]
    "Precipitation ground 6h": 450,  # [kg/m^2 s]
    "LI surface": 473,  # ['C]
    "CAPE surface": 474,  # [J/kg]
    "CIN surface": 475,  # [J/kg]
    "Pressure sea lvl": 586  # [Pa]
}

CHARTS = {
    "Wind gust ground": "Wind gust ground",
    "Wind 250hPa": "Wind 250hPa",
    "Temperature 2m": "Temperature 2m",
    "Dew point 2m": "Dew point 2m",
    "Wind 10m": "Wind 10m",
    # "Precipitation ground 6h": "Precipitation ground 6h",
    "LI surface": "LI surface",
    "CAPE surface": "CAPE surface",
    "CIN surface": "CIN surface",
    "Pressure sea lvl": "Pressure sea lvl"
}

CHARTS_NONZERO = {
    "Wind gust ground": "Wind gust ground",
    "Wind 250hPa": "Wind 250hPa",
    "Temperature 2m": "Temperature 2m",
    "Dew point 2m": "Dew point 2m",
    "Wind 10m": "Wind 10m",
    "Precipitation ground 6h": "Precipitation ground 6h",
    "LI surface": "LI surface",
    "CAPE surface": "CAPE surface",
    "CIN surface": "CIN surface",
    "Pressure sea lvl": "Pressure sea lvl"
}

FORECAST_HOURS = [0,   6,   12,  18,  24,  30,  36,  42,  48,  54,
                  60,  66,  72,  78,  84,  90,  96,  102, 108, 114,
                  120, 132, 144, 156, 168, 180, 192, 204, 216, 228,
                  240, 252, 264, 276, 288, 300, 312, 324, 336, 348,
                  360, 372, 384]


def choose_levels(chart: str):
    """
    Chooses levels and cmap for visualization. User can specify these parameters here.
    :param chart: chart name
    :return: levels and colormap for specified chart
    """
    arrange_levels = {
        "Wind gust ground":         np.arange(1, 50, 1),        # [m/s]
        "Wind 250hPa":              np.arange(1, 70, 2),        # [m/s]
        "Temperature 2m":           np.arange(-30, 42, 1),      # ['C]
        "Dew point 2m":             np.arange(-30, 42, 1),      # ['C]
        "Wind 10m":                 np.arange(1, 50, 1),        # [m/s]
        "Precipitation ground 6h":  np.arange(1, 41, 2),        # [kg/m^2 s]
        "LI surface":               np.arange(-11, 12, 0.5),    # ['C]
        "CAPE surface":             np.arange(100, 4000, 100),  # [J/kg]
        "CIN surface":              np.arange(-300, 0, 10),     # [J/kg]
        "Pressure sea lvl":         np.arange(950, 1060, 2)     # [hPa]
    }

    arrange_cmap = {
        "Wind gust ground":         'Blues',
        "Wind 250hPa":              'BuPu',
        "Temperature 2m":           'jet',
        "Dew point 2m":             'jet',
        "Wind 10m":                 'Blues',
        "Precipitation ground 6h":  'BuPu',
        "LI surface":               'RdBu_r',
        "CAPE surface":             'PuRd',
        "CIN surface":              'BuPu_r',
        "Pressure sea lvl":         'cool_r'
    }

    levels = arrange_levels[chart]
    cmap = arrange_cmap[chart]

    return levels, cmap


def gfs_scan_bands(filepath):
    """
    Helper function to scan through all bands in grib file and save their names into csv file.
    :param filepath: path to particular grib file.
    """
    grib = gdal.Open(filepath)
    with open("bands.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(1, grib.RasterCount):
            band = grib.GetRasterBand(i)
            writer.writerow([str(i), band.GetMetadata()['GRIB_COMMENT'], band.GetDescription()])
        csvfile.close()


def gfs_download_newest_data():

    url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    print("Getting the newest data...")
    print("Finding date and hour...")

    r = requests.get(url)
    urls = re.findall(regex, r.content.decode('utf-8'))
    url = urls[0][0]
    date = url[-8::]

    r = requests.get(url)
    urls = re.findall(regex, r.content.decode('utf-8'))
    hour = int((urls[0][0])[-2::])

    print("Found the newest data from: {date}, {hour} UTC.".format(date=date, hour=hour))

    path = os.path.join(DIRNAME, "data/gfs/{}/{:02}z".format(date, hour))
    if os.path.isdir(path) and len(os.listdir(path)) == len(FORECAST_HOURS):
        print("Data is already downloaded!")
        is_new_data = False
    else:
        print("Downloading data... It might take some minutes.")
        is_new_data = True

        for forecast in FORECAST_HOURS:
            try:
                gfs_get_raw_data(date, hour, forecast, EXTENT_POLAND)
            except EOFError:
                print("Data is not prepared yet!")
                is_new_data = False
                break

    # print("Data downloaded succesfully!")
    return date, hour, is_new_data


def gfs_get_raw_data(date: str, hour: int, forecast: int, extent: List[int]):
    """
    Gets raw GFS data for given date, hour and longitude and latitude extent.
    :param date: given date as string in format "YYYYMMDD"
    :param hour: given hour (UTC) as integer (available: 0, 6, 12, 18)
    :param forecast: given forecast hour as integer (available integers 0-392)
    :param extent: given extent as List[int] in format: [left_lon, right_lon, top_lat, bottom_lat]
    """

    if type(date) != str:
        raise TypeError("Date should be a string in format YYYYMMDD!")
    if type(hour) != int:
        raise TypeError("Hour should be one of integers: 0, 6, 12, 18!")
    if type(forecast) != int:
        raise TypeError("Forecast should be one of integers in range 0-392!")

    if len(date) != 8 or not date.isnumeric():
        raise ValueError("Date should be a string in format YYYYMMDD!")
    if hour not in [0, 6, 12, 18]:
        raise ValueError("Hour should be one of integers: 0, 6, 12, 18!")
    if forecast not in [num for num in range(0, 393)]:
        raise ValueError("Forecast should be one of integers in range 0-392!")
    if len(extent) != 4:
        raise ValueError("Extent should be a List of four integers!")

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    path = os.path.join(DIRNAME, "data/gfs/{}/{:02}z".format(date, hour))
    filename = "gfs.pgrb2.0p25.f{:03}".format(forecast)

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.isfile(os.path.join(path, filename)):
        print("Deleting old file.")
        os.remove(os.path.join(path, filename))

    url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{hour:02}z.pgrb2.0p25.f{forecast:03}&all_lev=on&all_var=on&subregion=&leftlon={left_lon}&rightlon={right_lon}&toplat={top_lat}&bottomlat={bottom_lat}&dir=%2Fgfs.{date}%2F{hour:02}"

    print("Trying to get data from {date} hour {hour:02}, forecast:{forecast:03}...".format(date=date, hour=hour, forecast=forecast))
    print("URL: " + url)
    print("File {filename} will be saved as {path}".format(filename=filename, path=path))

    r = requests.get(url)
    with open(os.path.join(path, filename), 'wb') as f:
        f.write(r.content)
        f.close()
        # for chunk in r.iter_content(chunk_size=1024*1024):
        #     if chunk:
        #         f.write(chunk)
        # f.close()

    size = os.path.getsize(os.path.join(path, filename))
    if size > 10*1024:
        print("File {filename} downloaded and saved at {path}.".format(filename=filename, path=path))
    else:
        print("File {filename} not downloaded!".format(filename=filename))
        raise EOFError


def matrix_resize(data_in: np.ndarray, factor: int) -> np.ndarray:
    """
    Resizes map/matrix to bigger one.
    :param data_in: matrix to be resized
    :param factor: multiplier
    :return: new matrix (np.array) with size data_in.shape*factor
    """
    result = np.zeros(np.array(data_in.shape)*factor)
    for i in range(data_in.shape[0]):
        for j in range(data_in.shape[1]):
            result[i*factor:(i+1)*factor, j*factor:(j+1)*factor] = data_in[i, j]

    return result


def gfs_prepare_raw_data_as_array(date: str, hour: int, forecast: int, chart: str) -> np.ndarray:
    """
    Opens grib file, takes raw data from it, makes resizing and average filtration on it and returns prepared matrix.
    :param date: given date as string in format "YYYYMMDD"
    :param hour: given hour (UTC) as integer (available: 0, 6, 12, 18)
    :param forecast: forecast hour as integer (available integers 0-392)
    :param band: number of band to indicate which data should be prepared (ref: bands_excel.xlsx) TODO: Update doc
    :param chart:
    :return prepared data matrix (np.array)
    """
    factor = 10

    if type(date) != str:
        raise TypeError("Date should be a string in format YYYYMMDD!")
    if type(hour) != int:
        raise TypeError("Hour should be one of integers: 0, 6, 12, 18!")
    if type(forecast) != int:
        raise TypeError("Forecast should be one of integers in range 0-392!")

    if len(date) != 8 or not date.isnumeric():
        raise ValueError("Date should be a string in format YYYYMMDD!")
    if hour not in [0, 6, 12, 18]:
        raise ValueError("Hour should be one of integers: 0, 6, 12, 18!")
    if forecast not in [num for num in range(0, 393)]:
        raise ValueError("Forecast should be one of integers in range 0-392!")
    if chart not in CHARTS.keys() and chart not in CHARTS_NONZERO.keys():
        raise ValueError("Chart should be one of CHARTS keys!")

    path = os.path.join(DIRNAME, "data/gfs/{}/{:02}z".format(date, hour))
    filename = "gfs.pgrb2.0p25.f{:03}".format(forecast)

    print("Opening file: {file}".format(file=filename))
    grib = gdal.Open(os.path.join(path, filename))

    print("Reading {} data.".format(chart))
    if chart in ["Wind 250hPa", "Wind 10m"]:
        if forecast == 0:
            data1 = grib.GetRasterBand(BANDS[CHARTS[chart]][0])
            data2 = grib.GetRasterBand(BANDS[CHARTS[chart]][1])
        else:
            data1 = grib.GetRasterBand(BANDS_NONZERO[CHARTS_NONZERO[chart]][0])
            data2 = grib.GetRasterBand(BANDS_NONZERO[CHARTS_NONZERO[chart]][1])
        data = (data1.ReadAsArray())**2 + (data2.ReadAsArray())**2
        data = np.sqrt(data*1.0)
        print("Band name:   {name}.\n".format(name=data1.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data1.GetDescription()))
        print("Band name:   {name}.\n".format(name=data2.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data2.GetDescription()))

    elif chart == "Pressure sea lvl":
        if forecast == 0:
            data = grib.GetRasterBand(BANDS[chart])
        else:
            data = grib.GetRasterBand(BANDS_NONZERO[chart])
        print("Band name:   {name}.\n".format(name=data.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data.GetDescription()))

        data = data.ReadAsArray() / 100.0
    else:
        if forecast == 0:
            data = grib.GetRasterBand(BANDS[chart])
        else:
            data = grib.GetRasterBand(BANDS_NONZERO[chart])
        print("Band name:   {name}.\n".format(name=data.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data.GetDescription()))

        data = data.ReadAsArray() * 1.0

    return convolve(matrix_resize(data, factor), np.ones([factor, factor])/(factor**2))


def gfs_visualize_gradient_map(data: np.ndarray, extent: List[int], chart: str):
    """
    Visualises prepared gfs matrix
    :param extent:
    :param data:
    :param chart:
    """
    if chart not in CHARTS.keys() and chart not in CHARTS_NONZERO.keys():
        raise ValueError("Chart should be one of CHARTS keys!")

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    # Prepare meshgrid
    x = np.linspace(left_lon, right_lon, data.shape[1])
    y = np.linspace(bottom_lat, top_lat, data.shape[0])
    xx, yy = np.meshgrid(x, y)

    # Prepare contour levels and colormap
    levels, cmap = choose_levels(chart)

    fig = plt.figure(figsize=(10.8, 7.2), dpi=200)

    bmap = Basemap(llcrnrlon=left_lon, urcrnrlon=right_lon, llcrnrlat=bottom_lat, urcrnrlat=top_lat, projection='cyl', resolution='i')
    bmap.drawcoastlines(linewidth=1.5)
    bmap.drawcountries(linewidth=1.5)
    if extent == EXTENT_POLAND:
        bmap.readshapefile('../shapefiles/POL_adm1', 'poland', linewidth=1.0)

    plt.contourf(xx[::-1], yy[::-1], data, alpha=0.9, cmap=cmap, levels=levels)
    S2 = plt.contour(xx[::-1], yy[::-1], data, alpha=0.8, colors='black', linewidths=0.5, levels=levels[::5])
    plt.clabel(S2, inline=0, inline_spacing=0, fontsize=12, fmt='%1.0f', colors='black')
    # plt.show()

    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    fig.savefig("{dir}/{chart}.png".format(dir=tempdir, chart=key), bbox_inches='tight')
    plt.close(fig)


# gfs_get_raw_data('20200722', 6, 0, [13, 25, 56, 48])
# simple_visualization('20200722', '06', [13, 25, 56, 48])
# gfs_scan_bands("gfs.t06z.pgrb2.0p25.f000")

# gfs_get_raw_data("20200728", 12, 0, EXTENT_POLAND)
# data = gfs_prepare_raw_data_as_array("20200728", 12, 0, 415)
# gfs_visualize_gradient_map(data, EXTENT_POLAND)

# start_time = time.time()
# gfs_download_newest_data()
# print("Execution time: {}".format(time.time()-start_time))

if __name__ == '__main__':
    # gfs_get_raw_data("20200819", 12, 0, EXTENT_POLAND)
    # gfs_scan_bands("{dir}/data/gfs/20200815/12z/gfs.pgrb2.0p25.f042".format(dir=DIRNAME))
    # data = gfs_prepare_raw_data_as_array("20200815", 12, 0, CHARTS["Temperature 2m"])
    # fig = gfs_visualize_gradient_map(data, EXTENT_POLAND, CHARTS["Temperature 2m"])
    # tempdir = "{dir}/data/pics/20200815/12z/test".format(dir=DIRNAME)
    # if not os.path.exists(tempdir):
    #     os.makedirs(tempdir)
    # fig.savefig("{dir}/{chart}.png".format(dir=tempdir, chart=CHARTS["Temperature 2m"]), bbox_inches='tight')

    while True:
        # 1. Download the newest data from NOAA servers
        date, hour, is_new_data = gfs_download_newest_data()

        # date = "20200820"
        # hour = 0
        # is_new_data = True

        # 2. Prepare data for each chart, build charts and save .png pics
        if is_new_data:
            for forecast in FORECAST_HOURS:
                if forecast == 0:
                    for key in CHARTS:
                        tempdir = '{dir}/data/pics/{date}/{hour:02}z/{forecast:03}'.format(dir=DIRNAME, date=date, hour=hour, forecast=forecast)
                        data = gfs_prepare_raw_data_as_array(date, hour, forecast, CHARTS[key])
                        gfs_visualize_gradient_map(data, EXTENT_POLAND, CHARTS[key])

                else:
                    for key in CHARTS_NONZERO:
                        tempdir = '{dir}/data/pics/{date}/{hour:02}z/{forecast:03}'.format(dir=DIRNAME, date=date, hour=hour, forecast=forecast)
                        data = gfs_prepare_raw_data_as_array(date, hour, forecast, CHARTS_NONZERO[key])
                        gfs_visualize_gradient_map(data, EXTENT_POLAND, CHARTS_NONZERO[key])

        time.sleep(30*60)

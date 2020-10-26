import os
import re
import time

os.environ["PROJ_LIB"] = "C:\\Python\\Anaconda\\Library\\share"
import requests, gdal, csv
import matplotlib.pyplot as plt
import numpy as np
import pickle
from mpl_toolkits.basemap import Basemap
from scipy.ndimage import convolve
from typing import List
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(__file__) + "/.."

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

CHARTS_NAMES = {
    "Wind gust ground":         "Wind gust at ground level",
    "Wind 250hPa":              "Average wind at 250[hPa]",
    "Temperature 2m":           "Average temperature at 2[m]",
    "Dew point 2m":             "Average dew point at 2[m]",
    "Wind 10m":                 "Average wind at 10[m]",
    "Precipitation ground 6h":  "Cumulative precipitation\n(last 6h)",
    "LI surface":               "Lifted index \nSurface based",
    "CAPE surface":             "Convective available potential energy\nSurface based",
    "CIN surface":              "Convective inhibition\nSurface based",
    "Pressure sea lvl":         "Pressure reduced to mean sea level"
}

FORECAST_HOURS = [0,   3,   6,   9,   12,  15,  18,  21,  24,  27,
                  30,  33,  36,  39,  42,  45,  48,  51,  54,  57,
                  60,  66,  72,  78,  84,  90,  96,  102, 108, 114,
                  120, 132, 144, 156, 168, 180, 192, 204, 216, 228,
                  240, 252, 264, 276, 288, 300, 312, 324, 336, 348,
                  360, 372, 384]

LEVELS = {
    "Wind gust ground":         np.arange(1, 40, 1),        # [m/s]
    "Wind 250hPa":              np.arange(1, 70, 2),        # [m/s]
    "Temperature 2m":           np.arange(-30, 42, 1),      # ['C]
    "Dew point 2m":             np.arange(-30, 42, 1),      # ['C]
    "Wind 10m":                 np.arange(1, 30, 1),        # [m/s]
    "Precipitation ground 6h":  np.arange(1, 41, 2),        # [kg/m^2 s]
    "LI surface":               np.arange(-15, 15, 0.5),    # ['C]
    "CAPE surface":             np.arange(100, 4000, 100),  # [J/kg]
    "CIN surface":              np.arange(-300, 0, 20),     # [J/kg]
    "Pressure sea lvl":         np.arange(950, 1060, 2)     # [hPa]
}


def choose_levels(chart: str):
    """
    Chooses levels and cmap for visualization. User can specify these parameters here.
    :param chart: chart name
    :return: levels and colormap for specified chart
    """

    if chart not in CHARTS.keys() and chart not in CHARTS_NONZERO.keys():
        raise ValueError("Incorrect chart!")

    arrange_cmap = {
        "Wind gust ground":         'BuPu',
        "Wind 250hPa":              'BuPu',
        "Temperature 2m":           'jet',
        "Dew point 2m":             'jet',
        "Wind 10m":                 'BuPu',
        "Precipitation ground 6h":  'BuPu',
        "LI surface":               'RdBu_r',
        "CAPE surface":             'PuRd',
        "CIN surface":              'BuPu_r',
        "Pressure sea lvl":         'cool_r'
    }

    levels = LEVELS[chart]
    cmap = arrange_cmap[chart]

    return levels, cmap


def gfs_scan_bands(filepath):
    """
    Helper function to scan through all bands in grib file and save their names into csv file.
    :param filepath: path to particular grib file.
    """

    if not os.path.isfile(filepath):
        raise ValueError("Wrong filepath - file not found!")

    grib = gdal.Open(filepath)
    with open("bands.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(1, grib.RasterCount):
            band = grib.GetRasterBand(i)
            writer.writerow([str(i), band.GetMetadata()['GRIB_COMMENT'], band.GetDescription()])
        csvfile.close()


def gfs_download_newest_data(forecasts: List[int] = FORECAST_HOURS, extent: List[int] = EXTENT_POLAND):
    """
    Checks if new data is availale on NCEP servers and downloads it.
    :param forecasts:
    :param extent:
    :return: Base date and hour of new data; flag if new data is downloaded completely.
    """
    url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

    print("Getting the newest data...")
    print("Finding date and hour...")

    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise ConnectionError

    urls = re.findall(regex, r.content.decode('utf-8'))
    url = urls[0][0]
    date = url[-8::]

    r = requests.get(url)
    urls = re.findall(regex, r.content.decode('utf-8'))
    hour = int((urls[0][0])[-2::])

    print("Found the newest data from: {date}, {hour} UTC.".format(date=date, hour=hour))

    path = os.path.join(BASE_DIR, "data/gfs/{}/{:02}z".format(date, hour))
    if os.path.isdir(path) and len(os.listdir(path)) == len(FORECAST_HOURS):
        print("Data is already downloaded!")
        is_new_data = False
    else:
        print("Downloading data... It might take some minutes.")
        is_new_data = True

        for forecast in forecasts:
            try:
                gfs_get_raw_data(date, hour, forecast, extent)
            except EOFError:
                print("Data is not prepared yet!")
                is_new_data = False
                break
            except FileExistsError:
                pass

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
        raise TypeError("Hour should be a type of integer!")
    if type(forecast) != int:
        raise TypeError("Forecast should be a type of integer!")
    if not isinstance(extent, list):
        raise TypeError("Extent should be a type of list of integers!")

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

    path = os.path.join(BASE_DIR, "data/gfs/{}/{:02}z".format(date, hour))
    filename = "gfs.pgrb2.0p25.f{:03}".format(forecast)

    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.isfile(os.path.join(path, filename)):
        size = os.path.getsize(os.path.join(path, filename))
        if size > 10 * 1024:
            raise FileExistsError("File already downloaded!")
        else:
            print("Deleting old file.")
            os.remove(os.path.join(path, filename))

    url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{hour:02}z.pgrb2.0p25.f{forecast:03}&all_lev=on&all_var=on&subregion=&leftlon={left_lon}&rightlon={right_lon}&toplat={top_lat}&bottomlat={bottom_lat}&dir=%2Fgfs.{date}%2F{hour:02}"

    print(f"\nTrying to get data from {date} hour {hour:02}, forecast:{forecast:03}...")
    print("URL: " + url)
    print("File {filename} will be saved at {path}".format(filename=filename, path=path))

    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise EOFError

    with open(os.path.join(path, filename), 'wb') as f:
        f.write(r.content)
        f.close()

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

    if type(factor) != int:
        raise TypeError("Factor should be an integer!")
    if factor <= 0:
        raise ValueError("Factor should be a positive integer!")

    result = np.zeros(np.array(data_in.shape)*factor)
    for i in range(data_in.shape[0]):
        for j in range(data_in.shape[1]):
            result[i*factor:(i+1)*factor, j*factor:(j+1)*factor] = data_in[i, j]

    return result


def gfs_build_visualization_map(date: str, hour: int, forecast: int, chart: str, extent: List[int] = EXTENT_POLAND,
                                img_path: str = BASE_DIR + "/data/pics/0"):
    """
    Prepares data, makes map with visualization and saves it to file.
    :param date:
    :param hour:
    :param forecast:
    :param chart:
    :param extent:
    :param path:
    """

    if type(date) != str:
        raise TypeError("Date should be a string in format YYYYMMDD!")
    if type(hour) != int:
        raise TypeError("Hour should be one of integers: 0, 6, 12, 18!")
    if type(forecast) != int:
        raise TypeError("Forecast should be one of integers in range 0-392!")
    if type(chart) != str:
        raise TypeError("Chart should be a string!")
    if not isinstance(extent, list):
        raise TypeError("Extent should be a type of list of integers!")
    if type(img_path) != str:
        raise TypeError("Path should be a string!")

    if len(date) != 8 or not date.isnumeric():
        raise ValueError("Date should be a string in format YYYYMMDD!")
    if hour not in [0, 6, 12, 18]:
        raise ValueError("Hour should be one of integers: 0, 6, 12, 18!")
    if forecast not in [num for num in range(0, 393)]:
        raise ValueError("Forecast should be one of integers in range 0-392!")
    if chart not in CHARTS.keys() and chart not in CHARTS_NONZERO.keys():
        raise ValueError("Chart should be one of CHARTS or CHARTS_NONZERO keys!")
    if len(extent) != 4:
        raise ValueError("Extent should be a List of four integers!")

    factor = 10

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    filedir = BASE_DIR + f"/data/gfs/{date}/{hour:02}z/"
    filename = f"gfs.pgrb2.0p25.f{forecast:03}"
    filepath = filedir + filename

    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Could not find particular GRIB file({filename}.")

    if os.path.isfile(f"{img_path}/{chart}.png"):
        raise FileExistsError(f"Demanded graph ({chart}.png)already exists.")

    print(f"Opening GRIB file: {filename}")
    grib = gdal.Open(filepath)

    print(f"Reading \"{chart}\" data.")
    if chart in ["Wind 250hPa", "Wind 10m"]:
        data_u = grib.GetRasterBand(BANDS[chart][0]) if forecast is 0 else grib.GetRasterBand(BANDS_NONZERO[chart][0])
        data_v = grib.GetRasterBand(BANDS[chart][1]) if forecast is 0 else grib.GetRasterBand(BANDS_NONZERO[chart][1])
        print("Band name:   {name}.\n".format(name=data_u.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data_u.GetDescription()))
        print("Band name:   {name}.\n".format(name=data_v.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data_v.GetDescription()))

        wind_u = data_u.ReadAsArray() * 1.0
        wind_v = data_v.ReadAsArray() * 1.0
        data = np.sqrt(wind_u ** 2 + wind_v ** 2)

        # wind_u = wind_u / data
        # wind_v = wind_v / data

        wind_u = convolve(matrix_resize((wind_u / data), factor), np.ones([factor, factor]) / (factor ** 2))
        wind_v = convolve(matrix_resize((wind_v / data), factor), np.ones([factor, factor]) / (factor ** 2))

    else:
        data = grib.GetRasterBand(BANDS[chart]) if forecast is 0 else grib.GetRasterBand(BANDS_NONZERO[chart])
        print("Band name:   {name}.\n".format(name=data.GetMetadata()['GRIB_COMMENT']) +
              "Description: {description}.".format(description=data.GetDescription()))

        data = data.ReadAsArray() * 1.0
        if chart == "Pressure sea lvl":
            data = data / 100.0

    data = convolve(matrix_resize(data, factor), np.ones([factor, factor]) / (factor ** 2))

    # TEMP
    # # ===============================================================================
    # fig = plt.figure(figsize=(10.8, 7.2), dpi=200)
    # plt.imshow(data, cmap='jet')
    # init_date = datetime.strptime(f"{date[:4]}/{date[4:6]}/{date[6:]} {hour:02}:00", '%Y/%m/%d %H:%M')
    # valid_date = init_date + timedelta(hours=forecast)
    # plt.legend([],
    #            title=f"{CHARTS_NAMES[chart]}\ninit:   {init_date.strftime('%Y/%m/%d %H:%M')} UTC\nvalid: {valid_date.strftime('%Y/%m/%d %H:%M')} UTC",
    #            loc="upper left")
    # fig.savefig("rawFilteredDataVis.png", bbox_inches='tight')
    # plt.close(fig)
    # # ===============================================================================

    # Prepare meshgrid
    x = np.linspace(left_lon, right_lon, data.shape[1])
    y = np.linspace(bottom_lat, top_lat, data.shape[0])
    xx, yy = np.meshgrid(x, y)

    # Prepare contour levels and colormap
    levels, cmap = choose_levels(chart)

    fig = plt.figure(figsize=(10.8, 7.2), dpi=200)

    # Prepare map contours
    bmap = prepare_basemap_pickle(extent)
    bmap.drawcoastlines(linewidth=1.5)
    bmap.drawcountries(linewidth=1.5)
    if extent == EXTENT_POLAND:
        bmap.readshapefile('../shapefiles/POL_adm1', 'poland', linewidth=1.0)

    # Plot data
    S1 = plt.contourf(xx[::-1], yy[::-1], data, alpha=0.9, cmap=cmap, levels=levels, extend='both')
    S2 = plt.contour(xx[::-1], yy[::-1], data, alpha=0.8, colors='black', linewidths=0.3, levels=levels)
    plt.clabel(S2, inline=0, inline_spacing=0, fontsize=15, fmt='%1.0f', colors='black')
    plt.colorbar(S1, orientation='vertical', fraction=0.0321, pad=0.005)

    init_date = datetime.strptime(f"{date[:4]}/{date[4:6]}/{date[6:]} {hour:02}:00", '%Y/%m/%d %H:%M')
    valid_date = init_date + timedelta(hours=forecast)

    plt.legend([], title=f"{CHARTS_NAMES[chart]}\ninit:   {init_date.strftime('%Y/%m/%d %H:%M')} UTC\nvalid: {valid_date.strftime('%Y/%m/%d %H:%M')} UTC", loc="upper left")

    if chart in ["Wind 250hPa", "Wind 10m"]:
        plt.quiver(xx[::20, ::20], yy[::20, ::20], wind_u[::20, ::20], wind_v[::20, ::20], scale=50, width=0.001)
    # plt.show()

    if not os.path.exists(img_path):
        os.makedirs(img_path)
    fig.savefig(f"{img_path}/{chart}.png", bbox_inches='tight')
    plt.close(fig)


def prepare_basemap_pickle(extent: List[int]):
    if not isinstance(extent, list):
        raise TypeError("Extent should be a type of list of integers!")
    if len(extent) != 4:
        raise ValueError("Extent should be a List of four integers!")

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    filedir = BASE_DIR + "/data/basemaps/"
    filename = filedir + f"bmap_{left_lon}-{right_lon}-{top_lat}-{bottom_lat}.pickle"

    if not os.path.isfile(filename):
        if not os.path.isdir(filedir):
            os.makedirs(filedir)
        bmap = Basemap(llcrnrlon=left_lon, urcrnrlon=right_lon, llcrnrlat=bottom_lat, urcrnrlat=top_lat, projection='cyl', resolution='i')
        pickle.dump(bmap, open(filename, 'wb'), -1)

    return pickle.load(open(filename, 'rb'))


if __name__ == '__main__':
    while True:
        # 1. Download the newest data from NOAA servers
        date, hour, is_new_data = gfs_download_newest_data()

        # date = "20200918"
        # hour = 12
        # is_new_data = True

        # 2. Prepare data for each chart, build charts and save .png pics
        if is_new_data:
            for forecast in FORECAST_HOURS:
                charts = CHARTS if forecast is 0 else CHARTS_NONZERO
                for key in charts:
                    try:
                        tempdir = '{dir}/data/pics/{date}/{hour:02}z/{forecast:03}'.format(dir=BASE_DIR, date=date,
                                                                                           hour=hour,
                                                                                           forecast=forecast)
                        gfs_build_visualization_map(date, hour, forecast, key, img_path=tempdir)
                    except (FileNotFoundError, FileExistsError):
                        pass
        print('''\n\n
        =======================================================\n
        =================={}==================
        ====== Newest charts are prepared and available! ======\n
        =======================================================\n
        '''.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        time.sleep(30*60)

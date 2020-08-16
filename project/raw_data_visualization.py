import os
import re

os.environ["PROJ_LIB"] = "C:\\Python\\Anaconda\\Library\\share"
import requests, gdal, csv
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from scipy.ndimage import convolve
from typing import List

DIRNAME = os.path.dirname(__file__)
EXTENT_POLAND = [13, 25, 56, 48]

BANDS = {
    "Wind gust ground": 11,        # [m/s]
    "u-component 250hPa": 146,     # [m/s]
    "v-component 250hPa": 147,     # [m/s]
    "Temperature 2m": 415,         # ['C]
    "Dew point 2m": 417,           # ['C]
    "u-component 10m": 420,        # [m/s]
    "v-component 10m": 421,        # [m/s]
    "Precipitation ground": 424,   # [kg/m^2 s]
    "LI surface": 432,             # ['C]
    "CAPE surface": 433,           # [J/kg]
    "CIN surface": 434,            # [J/kg]
    "Pressure sea lvl": 520        # [Pa]
}

CHARTS = {
    "Wind gust ground": "Wind gust ground",
    "Wind 250hPa": ["u-component 250hPa", "v-component 250hPa"],
    "Temperature 2m": "Temperature 2m",
    "Dew point 2m": "Dew point 2m",
    "Wind 10m": ["u-component 10m", "v-component 10m"],
    "Precipitation ground": "Precipitation ground",
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


def choose_levels(band: str):
    """
    Chooses levels and cmap for visualization
    :param band: band name
    :return: levels and colormap
    """
    arrange_levels = {
        "Wind gust ground": np.arange(5, 50, 1),
        # "u-component 250hPa": 146,
        # "v-component 250hPa": 147,
        "Temperature 2m": np.arange(-30, 42, 1),
        "Dew point 2m": np.arange(-30, 42, 1),
        # "u-component 10m": np.arange(0, 35, 1),
        # "v-component 10m": np.arange(0, 35, 1),
        "Precipitation ground": np.arange(0, 100, 1),
        "LI surface": np.arange(-11, 12, 0.5),
        "CAPE surface": np.arange(100, 4000, 100),
        "CIN surface": np.arange(-300, 0, 5),
        "Pressure sea lvl": np.arange(900, 1150, 2)
    }

    arrange_cmap = {
        "Wind gust ground": np.arange(5, 50, 1),    # TODO: set correct colormap
        # "u-component 250hPa": 146,
        # "v-component 250hPa": 147,
        "Temperature 2m": 'jet',
        "Dew point 2m": 'jet',
        # "u-component 10m": np.arange(0, 35, 1),
        # "v-component 10m": np.arange(0, 35, 1),
        "Precipitation ground": 'BuPu',
        "LI surface": 'RdBu_r',
        "CAPE surface": 'PuRd',
        "CIN surface": 'BuPu_r',
        "Pressure sea lvl": 'cool_r'
    }

    levels = arrange_levels[band]
    cmap = arrange_cmap[band]

    return levels, cmap


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

    if len(date) != 8:
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
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
        f.close()

    if os.path.getsize(os.path.join(path, filename)):
        print("File {filename} downloaded and saved at {path}.".format(filename=filename, path=path))
    else:
        print("File {filename} not downloaded!".format(filename=filename))


def gfs_scan_bands(filepath):
    """
    Scans through all bands in grib file and saves their names into csv file.
    :param filepath: path to particular grib file.
    """
    grib = gdal.Open(filepath)
    with open("bands.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(1, grib.RasterCount):
            band = grib.GetRasterBand(i)
            writer.writerow([str(i), band.GetMetadata()['GRIB_COMMENT'], band.GetDescription()])
        csvfile.close()


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


def gfs_prepare_raw_data_as_array(date: str, hour: int, forecast: int, band: int) -> np.ndarray:
    """
    Opens grib file, takes raw data from it, makes resizing and average filtration on it and returns prepared matrix.
    :param date: given date as string in format "YYYYMMDD"
    :param hour: given hour (UTC) as integer (available: 0, 6, 12, 18)
    :param forecast: forecast hour as integer (available integers 0-392)
    :param band: number of band to indicate which data should be prepared (ref: bands_excel.xlsx)
    :return prepared data matrix (np.array)
    """
    factor = 50

    path = os.path.join(DIRNAME, "data/gfs/{}/{:02}z".format(date, hour))
    filename = "gfs.pgrb2.0p25.f{:03}".format(forecast)

    grib = gdal.Open(os.path.join(path, filename))
    data = grib.GetRasterBand(band)
    print("Band name:   {name}.\n".format(name=data.GetMetadata()['GRIB_COMMENT']) +
          "Description: {description}.".format(description=data.GetDescription()))
    # TODO: find faster solution than convolve()
    return convolve(matrix_resize(data.ReadAsArray(), factor), np.ones([factor, factor])/(factor**2))


def gfs_visualize_gradient_map(data: np.ndarray, extent: List[int], chart: str):
    """
    Visualises prepared gfs matrix
    :param extent:
    :param data:
    :param chart:
    """

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    if chart in ["Wind 250hPa", "Wind 10m"]:
        raise NotImplementedError   # TODO: implement wind case
    else:
        levels, cmap = choose_levels(CHARTS[chart])

    x = np.linspace(left_lon, right_lon, data.shape[1])
    y = np.linspace(bottom_lat, top_lat, data.shape[0])
    xx, yy = np.meshgrid(x, y)

    fig = plt.figure(figsize=(10.8, 7.2), dpi=200)

    bmap = Basemap(llcrnrlon=left_lon, urcrnrlon=right_lon, llcrnrlat=bottom_lat, urcrnrlat=top_lat, projection='cyl', resolution='i')
    bmap.drawcoastlines(linewidth=1.5)
    bmap.drawcountries(linewidth=1.5)
    bmap.readshapefile('POL_adm1', 'poland', linewidth=1.0)

    plt.contourf(xx[::-1], yy[::-1], data, alpha=0.9, cmap=cmap, levels=levels)
    S2 = plt.contour(xx[::-1], yy[::-1], data, alpha=0.8, colors='black', linewidths=0.5, levels=levels)
    plt.clabel(S2, inline=0, inline_spacing=0, fontsize=12, fmt='%1.0f', colors='black')
    # plt.show()
    return fig
    # fig.savefig('test8.png')


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
        return

    print("Downloading data...")
    for forecast in FORECAST_HOURS:
        gfs_get_raw_data(date, hour, forecast, EXTENT_POLAND)


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
    data = gfs_prepare_raw_data_as_array("20200815", 12, 0, BANDS["CAPE surface"])
    fig = gfs_visualize_gradient_map(data, EXTENT_POLAND, "CAPE surface")
    fig.savefig('test8.png', bbox_inches='tight')
    # gfs_download_newest_data()

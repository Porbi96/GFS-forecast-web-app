import os
os.environ["PROJ_LIB"] = "C:\\Python\\Anaconda\\Library\\share"
import requests, gdal, csv
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from scipy.ndimage import convolve
from pathlib import Path
from typing import List

EXTENT_POLAND = [13, 25, 56, 48]
DIRNAME = os.path.dirname(__file__)

def gfs_get_raw_data(date: str, hour: int, forecast: int, extent: List[int]):
    """
    Gets raw GFS data for given date, hour and longitude and latitude extent.
    :param date: given date as string in format "YYYYMMDD"
    :param hour: given hour (UTC) as integer (available: 0, 6, 12, 18)
    :param forecast: given forecast hour as integer (available integers 0-392)
    :param extent: given extent as List[int] in format: [left_lon, right_lon, top_lat, bottom_lat]
    """

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

    # url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t" + hour + "z.pgrb2.0p25.f000&all_lev=on" \
    #       "&all_var=on&subregion=&leftlon=13&rightlon=25&toplat=56&bottomlat=48&dir=%2Fgfs." + date + '%2F' + hour

    print("Trying to get data from {date} hour {hour:02}, forecast:{forecast:03}...".format(date=date, hour=hour, forecast=forecast))
    print("URL: " + url)
    print("File {filename} will be saved as {path}".format(filename=filename, path=path))

    r = requests.get(url)
    with open(os.path.join(path, filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        f.close()

    if os.path.getsize(os.path.join(path, filename)):
        print("File {filename} downloaded and saved at {path}.".format(filename=filename, path=path))
    else:
        print("File {filename} not downloaded!".format(filename=filename))


def gfs_scan_bands(filepath):
    """

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


def gfs_visualize_gradient_map(data: np.ndarray, extent: List[int]):
    """
    Visualises prepared gfs matrix
    :param extent:
    :param data:
    """
    # filename = 'gfs.t' + hour + 'z.pgrb2.0p25.f000'
    #
    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    # # for i in range(400, 450):
    # #     band = grib.GetRasterBand(i)
    # #
    # #     print("band no " + str(i) + " name: " + band.GetMetadata()['GRIB_COMMENT'])
    # #     print("band description: " + band.GetDescription())
    # grib = gdal.Open(filename)
    # band = grib.GetRasterBand(415)
    # print("band name: " + band.GetMetadata()['GRIB_COMMENT'])
    # print("band description: " + band.GetDescription())
    #
    # data = band.ReadAsArray()
    # scaled_data = map_resize(data, 50)
    # final_data = convolve(scaled_data, np.ones([50, 50])/2500)

    levels = np.arange(-30, 42, 1)
    x = np.linspace(left_lon, right_lon, data.shape[1])
    y = np.linspace(bottom_lat, top_lat, data.shape[0])
    xx, yy = np.meshgrid(x, y)

    bmap = Basemap(llcrnrlon=left_lon, urcrnrlon=right_lon, llcrnrlat=bottom_lat, urcrnrlat=top_lat, projection='cyl', resolution='i')
    bmap.drawcoastlines(linewidth=1.5)
    bmap.drawcountries(linewidth=1.5)
    bmap.readshapefile('POL_adm1', 'poland', linewidth=1.0)

    plt.contourf(xx[::-1], yy[::-1], data, alpha=0.9, cmap='jet', levels=levels)
    S2 = plt.contour(xx[::-1], yy[::-1], data, alpha=0.8, colors='black', linewidths=0.5, levels=levels)
    plt.clabel(S2, inline=0, inline_spacing=0, fontsize=20, fmt='%1.0f', colors='black')
    plt.show()
    # plt.imsave('test8.png', S_mixed)


# gfs_get_raw_data('20200722', 6, 0, [13, 25, 56, 48])
# simple_visualization('20200722', '06', [13, 25, 56, 48])
# gfs_scan_bands("gfs.t06z.pgrb2.0p25.f000")

# gfs_get_raw_data("20200728", 12, 0, EXTENT_POLAND)
data = gfs_prepare_raw_data_as_array("20200728", 12, 0, 415)
gfs_visualize_gradient_map(data, EXTENT_POLAND)

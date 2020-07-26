import requests, os, gdal, csv
os.environ["PROJ_LIB"] = "C:\\Python\\Anaconda\\Library\\share"
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from scipy.ndimage import convolve
from typing import List


def gfs_get_raw_data(date: str, hour: int, forecast: int, extent: List[int]):
    """
    Gets raw GFS data for given date, hour and longitude and latitude extent.
    :param date: given date as string in format "YYYYMMDD"
    :param hour: given hour (UTC) as integer (available: 0, 6, 12, 18)
    :param forecast: given forecast hour as string in format "HHH" (available integers 000-392)
    :param extent: given extent as List[int] in format: [left_lon, right_lon, top_lat, bottom_lat]
    """

    left_lon = extent[0]
    right_lon = extent[1]
    top_lat = extent[2]
    bottom_lat = extent[3]

    filepath = "../data/gfs/{}/{:02}z/gfs.pgrb2.0p25.f{:03}".format(date, hour, forecast)

    if os.path.isfile(filepath):
        print("Deleting old file.")
        os.remove(filepath)

    url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{hour:02}z.pgrb2.0p25.f{forecast:03}&all_lev=on&all_var=on&subregion=&leftlon={left_lon}&rightlon={right_lon}&toplat={top_lat}&bottomlat={bottom_lat}&dir=%2Fgfs.{date}%2F{hour:02}"

    # url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t" + hour + "z.pgrb2.0p25.f000&all_lev=on" \
    #       "&all_var=on&subregion=&leftlon=13&rightlon=25&toplat=56&bottomlat=48&dir=%2Fgfs." + date + '%2F' + hour

    print("Trying to get data from {date} hour {hour:02}, forecast:{forecast:03}...".format(date=date, hour=hour, forecast=forecast))
    print("URL: " + url)

    r = requests.get(url)
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
        f.close()

    if os.path.getsize(filepath):
        print("File downloaded and saved at {path}.".format(path=filepath))
    else:
        print("File not downloaded!")


def gfs_scan_bands(filepath):
    """

    :param filepath:
    """
    grib = gdal.Open(filepath)
    with open("bands.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(1, grib.RasterCount):
            band = grib.GetRasterBand(i)
            writer.writerow([str(i), band.GetMetadata()['GRIB_COMMENT'], band.GetDescription()])
        csvfile.close()


def map_resize(data_in, factor):
    result = np.zeros(np.array(data_in.shape)*factor)
    for i in range(data_in.shape[0]):
        for j in range(data_in.shape[1]):
            result[i*factor:(i+1)*factor, j*factor:(j+1)*factor] = data_in[i, j]

    return result


def gfs_prepare_raw_data_as_array(date: str, hour: int, forecast: int, band: int):
    factor = 50

    filepath = "../data/gfs/{}/{:02}z/gfs.pgrb2.0p25.f{:03}".format(date, hour, forecast)

    grib = gdal.Open(filepath)
    data = grib.GetRasterBand(band)
    print("Band name: {name}.\n".format(name=data.GetMetadata()['GRIB_COMMENT']) +
          "Description: {description}.".format(description=data.GetDescription()))

    return convolve(map_resize(data.ReadAsArray(), factor), np.ones([factor, factor])/(factor**2))


def gfs_visualize_gradient_map(date: str, hour: int, forecast: int, extent: List[int]):
    """
    Builds gradient map from raw GFS data.
    :param date:
    :param hour:
    :param forecast:
    :param extent:
    """
    filename = 'gfs.t' + hour + 'z.pgrb2.0p25.f000'

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
    x = np.linspace(left_lon, right_lon, final_data.shape[1])
    y = np.linspace(bottom_lat, top_lat, final_data.shape[0])
    xx, yy = np.meshgrid(x,y)

    # ax = plt.figure()
    bmap = Basemap(llcrnrlon=left_lon, urcrnrlon=right_lon, llcrnrlat=bottom_lat, urcrnrlat=top_lat, projection='cyl', resolution='i')
    bmap.drawcountries()
    bmap.drawcoastlines()
    # plt.show()

    plt.contourf(xx[::-1], yy[::-1], final_data, alpha=1, cmap='jet', levels=levels)
    S2 = plt.contour(xx[::-1], yy[::-1], final_data, alpha=0.8, colors='black', linewidths=0.5, levels=levels)
    plt.clabel(S2, inline=0, inline_spacing=0, fontsize=20, fmt='%1.0f', colors='black')
    plt.show()
    # plt.imsave('test8.png', S_mixed)


# gfs_get_raw_data('20200722', 6, 0, [13, 25, 56, 48])
# simple_visualization('20200722', '06', [13, 25, 56, 48])
gfs_scan_bands("gfs.t06z.pgrb2.0p25.f000")

import os
import unittest
import numpy as np
import datetime
from project import raw_data_visualization as rdv


class TestRawDataVisualization(unittest.TestCase):
    def test_choose_levels_temp_levels(self):
        levels, cmap = rdv.choose_levels("Temperature 2m")
        self.assertEqual(len(levels), len([num for num in range(-30, 42)]))
        self.assertEqual(cmap, 'jet')

    def test_choose_levels_wrong_chart_name(self):
        self.assertRaises(ValueError, lambda: rdv.choose_levels("Random chart name"))

    def test_gfs_scan_bands_wrong_filepath(self):
        self.assertRaises(ValueError, lambda: rdv.gfs_scan_bands("../a/b/c.f000"))

    def test_gfs_scan_bands_correct_input(self):
        if os.path.isfile("bands.csv"):
            os.remove("bands.csv")
        rdv.gfs_scan_bands(f"{rdv.BASE_DIR}/testGrib.f000")
        self.assertTrue(lambda: os.path.isfile("bands.csv"))

    def test_download_newest_data(self):
        date, hour, is_new_data = rdv.gfs_download_newest_data([0, 3])
        self.assertEqual(date, datetime.date.today().strftime("%Y%m%d"))
        self.assertTrue(is_new_data)

    def test_gfs_get_raw_data(self):
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data(20200816, 12, 0, rdv.EXTENT_POLAND))
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data("20200816", "12", 0, rdv.EXTENT_POLAND))
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data("20200816", 12, "0", rdv.EXTENT_POLAND))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("20200816", 1, 0, rdv.EXTENT_POLAND))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("2020081", 0, 0, rdv.EXTENT_POLAND))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("d0200811", 0, 0, rdv.EXTENT_POLAND))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("20200816", 0, 400, rdv.EXTENT_POLAND))
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data("20200816", 10, 0, 5))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("20200816", 10, 0, [5, 10]))

    def test_matrix_resize_if_correct_resizing(self):
        array1 = np.array([[0, 1], [1, 0]])
        array2 = np.array([[0, 0, 1, 1], [0, 0, 1, 1], [1, 1, 0, 0], [1, 1, 0, 0]])
        self.assertTrue((rdv.matrix_resize(array1, 2) == array2).all())

    def test_matrix_resize_assert_error(self):
        self.assertRaises(TypeError, lambda: rdv.matrix_resize([0], 5.5))
        self.assertRaises(TypeError, lambda: rdv.matrix_resize([0], [5]))
        self.assertRaises(ValueError, lambda: rdv.matrix_resize([0], -5))
        self.assertRaises(ValueError, lambda: rdv.matrix_resize([0], 0))

    def test_gfs_build_visualization_map_bad_values(self):
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, "Bad Chart Name"))
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("2020", 12, 0, "Temperature 2m"))
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("NotANumb", 12, 0, "Temperature 2m"))
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("20200820", 1, 0, "Temperature 2m"))
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 1000, "Temperature 2m"))
        self.assertRaises(ValueError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, "Temperature 2m",
                                                                              extent=[1, 1, 1]))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, "Temperature 2m",
                                                                              extent=5))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, "Temperature 2m",
                                                                              img_path=5))
        self.assertRaises(FileNotFoundError, lambda: rdv.gfs_build_visualization_map("30200820", 12, 0,
                                                                                     "Temperature 2m"))

    def test_gfs_build_visualization_map_bad_types(self):
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map(20200820, 12, 0, "Temperature 2m"))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", "12", 0, "Temperature 2m"))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, "0", "Temperature 2m"))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, 2))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, extent=5))
        self.assertRaises(TypeError, lambda: rdv.gfs_build_visualization_map("20200820", 12, 0, img_path=10))

    def test_prepare_basemap_pickle(self):
        self.assertRaises(TypeError, lambda: rdv.prepare_basemap_pickle(20))
        self.assertRaises(ValueError, lambda: rdv.prepare_basemap_pickle([20, 10]))

    def test_prepare_basemap_pickle_should_pass(self):
        raised = False
        try:
            rdv.prepare_basemap_pickle(rdv.EXTENT_POLAND)
        except:
            raised = True
        self.assertEqual(False, raised)


if __name__ == '__main__':
    unittest.main()

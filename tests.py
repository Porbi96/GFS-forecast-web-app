import unittest
import numpy as np
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

    def test_gfs_get_raw_data(self):
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data(20200816, 12, 0, rdv.EXTENT_POLAND))
        self.assertRaises(ValueError, lambda: rdv.gfs_get_raw_data("20200816", 1, 0, rdv.EXTENT_POLAND))
        self.assertRaises(TypeError, lambda: rdv.gfs_get_raw_data("20200816", 10, 0, 5))

    def test_matrix_resize_if_correct_resizing(self):
        array1 = np.array([[0, 1], [1, 0]])
        array2 = np.array([[0, 0, 1, 1], [0, 0, 1, 1], [1, 1, 0, 0], [1, 1, 0, 0]])
        self.assertTrue((rdv.matrix_resize(array1, 2) == array2).all())

    def test_matrix_resize_assert_error(self):
        self.assertRaises(TypeError, lambda: rdv.matrix_resize([0], 5.5))
        self.assertRaises(TypeError, lambda: rdv.matrix_resize([0], [5]))
        self.assertRaises(ValueError, lambda: rdv.matrix_resize([0], -5))
        self.assertRaises(ValueError, lambda: rdv.matrix_resize([0], 0))

    def test_gfs_prepare_raw_data_as_array(self):
        self.assertRaises(ValueError, lambda: rdv.gfs_prepare_raw_data_as_array("20200816", 12, 0, "Random Chart Name"))
        self.assertRaises(ValueError, lambda: rdv.gfs_prepare_raw_data_as_array("20200816", 12, 1000, rdv.CHARTS["Temperature 2m"]))
        self.assertRaises(ValueError, lambda: rdv.gfs_prepare_raw_data_as_array("20200816", 1000, 0, rdv.CHARTS["Temperature 2m"]))
        self.assertRaises(ValueError, lambda: rdv.gfs_prepare_raw_data_as_array("202008169", 12, 0, rdv.CHARTS["Temperature 2m"]))
        self.assertRaises(ValueError, lambda: rdv.gfs_prepare_raw_data_as_array("NotANumb", 12, 0, rdv.CHARTS["Temperature 2m"]))

    def test_gfs_visualize_gradient_map(self):
        self.assertRaises(ValueError, lambda: rdv.gfs_visualize_gradient_map(np.array([[0, 1], [1, 0]]), rdv.EXTENT_POLAND, "Test-ShouldRaiseValueError"))
        self.assertRaises(ValueError, lambda: rdv.gfs_visualize_gradient_map(np.array([[0, 1], [1, 0]]), rdv.EXTENT_POLAND[:3], rdv.CHARTS["Temperature 2m"]))
        self.assertRaises(TypeError, lambda: rdv.gfs_visualize_gradient_map(np.array([[0, 1], [1, 0]]), 1, rdv.CHARTS["Temperature 2m"]))
        self.assertRaises(TypeError, lambda: rdv.gfs_visualize_gradient_map(np.array([[0, 1], [1, 0]]), rdv.EXTENT_POLAND[:3], 1))


if __name__ == '__main__':
    unittest.main()

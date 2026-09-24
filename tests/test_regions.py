import unittest

from genesysmod_iamc.regions import compact_connection, normalize_region


class ConnectionRegionTests(unittest.TestCase):
    def test_shared_hierarchy(self):
        self.assertEqual(compact_connection("Senegal|Dakar>Senegal|Thiès"),
                         "Senegal|Dakar>Thiès")

    def test_other_names_are_preserved(self):
        for value in ("World", "Senegal|Dakar", "Dakar>Thiès",
                      "Senegal|Dakar>Thiès", "Senegal|Dakar>Other|City"):
            with self.subTest(value=value):
                self.assertEqual(compact_connection(value), value)

    def test_output_prefix(self):
        for value in ("Dakar>Thiès", "Senegal|Dakar>Senegal|Thiès",
                      "Senegal|Dakar>Thiès"):
            with self.subTest(value=value):
                self.assertEqual(normalize_region(value, "Senegal"), "Senegal|Dakar>Thiès")

    def test_thies_spelling_is_normalized(self):
        self.assertEqual(normalize_region("Thies", "Senegal"), "Senegal|Thiès")

import tempfile
import unittest
from pathlib import Path
import pandas as pd
from genesysmod_iamc.converter import (
    build_summary,
    convert,
    load_excluded_variables,
    prepare_export,
)

REFERENCE = Path('/home/ahmany/om4a/p4rdata/data/SN_BAU_2030')

class ConverterTests(unittest.TestCase):
    def test_profile_uses_canonical_synthetic_methane_spelling(self):
        profile = Path(__file__).parents[1] / 'src/genesysmod_iamc/profiles/conversion.yaml'
        text = profile.read_text()
        self.assertNotIn('Synthetic methane', text)
        self.assertIn('Synthetic Methane', text)

    def test_profile_uses_requested_model_version(self):
        profile = Path(__file__).parents[1] / 'src/genesysmod_iamc/profiles/conversion.yaml'
        self.assertIn('Model: GENeSYS-MOD v3.1', profile.read_text())

    def test_public_export_policy(self):
        excluded = next(iter(load_excluded_variables()))
        frame = pd.DataFrame([
            ['GENeSYS-MOD v3.1', 'scenario', 'World', 'Capacity|Electricity', 'GW', 2030, 1],
            ['GENeSYS-MOD v3.1', 'scenario', 'Dakar>Thiès', 'Capacity|Electricity', 'GW', 2030, 2],
            ['GENeSYS-MOD v3.1', 'scenario', 'Dakar', excluded, 'GW', 2030, 3],
            ['GENeSYS-MOD v3.1', 'scenario', 'Dakar', 'Capacity|Electricity', 'GW', 2030, 4],
        ], columns=['Model', 'Scenario', 'Region', 'Variable', 'Unit', 'Year', 'Value'])
        result = prepare_export(frame, {'global_region': 'World'}, 'Senegal')
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0].Region, 'Senegal|Dakar')
        self.assertEqual(result.iloc[0].Variable, 'Capacity|Electricity')

    def test_frozen_exclusion_list_contains_179_variables(self):
        self.assertEqual(len(load_excluded_variables()), 179)

    def test_combined_summary_describes_export_content(self):
        frame = pd.DataFrame([
            ['GENeSYS-MOD v3.1', 'scenario', 'Senegal|Dakar',
             'Capacity|Electricity|Solar', 'GW', 2030, 1],
            ['GENeSYS-MOD v3.1', 'scenario', 'Senegal|Dakar',
             'Capacity|Electricity|Solar', 'GW', 2040, 2],
        ], columns=['Model', 'Scenario', 'Region', 'Variable', 'Unit', 'Year', 'Value'])
        summary = build_summary(frame)
        self.assertIn('| Variables | 1 |', summary)
        self.assertIn('| Non-empty annual observations | 2 |', summary)
        self.assertIn('| Capacity | 1 |', summary)
        self.assertIn('**Years:** 2030, 2040', summary)
        self.assertIn('Installed electricity capacity', summary)
        self.assertIn('does not report utilization', summary)

    def test_outputs_require_input_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, '--input-file'):
                convert('outputs', folder, folder)

    @unittest.skipUnless(
        (REFERENCE / 'GENeSYS-MOD/inputs/input_data_senegal_BAU_v2.xlsx').exists(),
        'Local regression dataset required',
    )
    def test_reference_parity_and_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            source = REFERENCE / 'GENeSYS-MOD/inputs/input_data_senegal_BAU_v2.xlsx'
            output = Path(folder)
            inputs, _ = convert('inputs', source, output)
            combined, _ = convert('outputs', REFERENCE / 'GENeSYS-MOD/outputs', output, source)
            # Repeat in the same folder, exercising replacement of existing files.
            convert('inputs', source, output)
            actual = pd.read_excel(output / 'combined_iamc.xlsx')
            self.assertEqual(set(actual.Model), {'GENeSYS-MOD v3.1'})
            self.assertFalse(actual.Region.eq('World').any())
            self.assertFalse(actual.Region.str.contains('>', regex=False).any())
            self.assertTrue(set(actual.Variable).isdisjoint(load_excluded_variables()))
            self.assertEqual(set(combined.Variable), set(actual.Variable))
            self.assertFalse((output / 'combined_iamc.csv').exists())
            self.assertFalse((output / 'outputs_iamc.xlsx').exists())
            self.assertFalse((output / 'outputs_summary.json').exists())
            self.assertTrue((output / 'combined_iamc_summary.md').exists())

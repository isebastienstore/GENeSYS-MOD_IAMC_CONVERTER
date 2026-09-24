import unittest
from unittest.mock import patch
from genesysmod_iamc.cli import main

class CliTests(unittest.TestCase):
    def test_success_exit_code(self):
        for kind in ('inputs', 'outputs'):
            with self.subTest(kind=kind), patch('genesysmod_iamc.cli.convert',
                return_value=(None, {'observations': 1, 'variables': 1})) as convert, patch('builtins.print'):
                self.assertEqual(main([kind, 'source', '--output', 'out']), 0)
                self.assertEqual(convert.call_args.args[0], kind)

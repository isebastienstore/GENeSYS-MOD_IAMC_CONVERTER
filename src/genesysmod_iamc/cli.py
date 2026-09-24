import argparse
from pathlib import Path

from .converter import convert


def main(argv=None):
    parser = argparse.ArgumentParser(prog='genesysmod-iamc')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('inputs', 'outputs'):
        command = sub.add_parser(name)
        command.add_argument('source', type=Path)
        command.add_argument('--output', required=True, type=Path)
        command.add_argument('--settings', type=Path, help='Conversion profile in YAML format')
        command.add_argument('--input-file', type=Path, help='Input workbook required for outputs')
        command.add_argument('--region-prefix', default='Senegal')
        command.add_argument('--project', type=Path, help='Accepted for compatibility; no nomenclature mapping is applied')
        command.add_argument('--allow-unmapped', action='store_true', help='Accepted for compatibility; profile selection is used')
    args = parser.parse_args(argv)
    try:
        _, summary = convert(args.command, args.source, args.output,
                             args.input_file, args.settings, args.region_prefix)
    except (ValueError, FileNotFoundError, KeyError) as error:
        parser.error(str(error))
    print(f"Export generated in {args.output}: {summary['observations']} observations, {summary['variables']} variables")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

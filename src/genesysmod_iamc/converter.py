"""Orchestrate the configurable GENeSYS-MOD to IAMC conversion."""
import copy
import hashlib
from pathlib import Path

import pandas as pd
import yaml

from .engine import run
from .regions import normalize_region

DEFAULT_SETTINGS = Path(__file__).parent / 'profiles/conversion.yaml'
DEFAULT_EXCLUDED_VARIABLES = Path(__file__).parent / 'profiles/excluded_variables.txt'

INDEX = ['Model', 'Scenario', 'Region', 'Variable', 'Unit', 'Year']


def load_excluded_variables(path=DEFAULT_EXCLUDED_VARIABLES):
    """Load the frozen set of IAMC variables excluded from public exports."""
    return {
        line.strip()
        for line in Path(path).read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    }


def prepare_export(frame, cfg, region_prefix):
    """Apply the final public-export policy before reshaping IAMC data."""
    frame = frame[INDEX + ['Value']].copy()
    removed = cfg.get('removed_variables', [])
    frame = frame[~frame.Variable.map(
        lambda value: any(
            value.startswith(pattern[:-1]) if pattern.endswith('|') else value == pattern
            for pattern in removed
        )
    )]
    frame = frame[~frame['Variable'].isin(load_excluded_variables())]
    frame['Region'] = frame['Region'].map(lambda value: normalize_region(value, region_prefix))
    frame = frame[
        frame['Region'].ne(cfg.get('global_region', 'World'))
        & ~frame['Region'].str.contains('>', regex=False, na=False)
    ]
    frame = frame.drop_duplicates().sort_values(INDEX).reset_index(drop=True)
    if frame.duplicated(INDEX).any():
        raise ValueError('The conversion produced contradictory IAMC rows')
    return frame


def rule_kind(name, rule):
    if rule.get('source') == 'input':
        return 'inputs'
    if rule.get('source') == 'internal' and name in (
        'Capital Cost Storage per Capacity|', 'Capital Cost|'
    ):
        return 'inputs'
    return 'outputs'


def convert(kind, source, output, input_file=None, settings=None, region_prefix='Senegal'):
    source, output = Path(source), Path(output)
    settings = Path(settings) if settings else DEFAULT_SETTINGS
    cfg = yaml.safe_load(settings.read_text())
    cfg['debug'] = []
    cfg['InteractiveMode'] = False
    all_rules = copy.deepcopy(cfg['variables'])
    if kind == 'inputs':
        input_file = source
        cfg['variables'] = {k: v for k, v in all_rules.items() if rule_kind(k, v) == 'inputs'}
    elif input_file is None:
        raise ValueError('Output conversion requires --input-file for input-dependent calculations')
    input_file = Path(input_file)
    data = pd.Series(dtype=object)
    names = {alt: main for main, alts in cfg['Scenarios'].items() for alt in alts}
    with pd.ExcelFile(input_file) as book:
        for sheet in cfg['genesys_datafiles']['input']['Sheets']:
            if sheet not in book.sheet_names:
                required_sheets = {s for rule in cfg['variables'].values() for s in rule.get('sheets', [])}
                if sheet in required_sheets or sheet == 'Sets':
                    raise ValueError(f'Missing required input sheet: {sheet}')
                continue
            frame = pd.read_excel(book, sheet_name=sheet)
            frame = frame[[c for c in frame.columns if not str(c).startswith('Unnamed')]]
            if 'Scenario' not in frame and 'PathwayScenario' not in frame:
                frame['Scenario'] = cfg['Scenario']
            frame = frame.rename(columns={'PathwayScenario': 'Scenario'})
            data.at['input_' + sheet] = frame
    if kind == 'outputs':
        required = {r.get('source') for r in all_rules.values()} - {'input', 'internal', None}
        for key in required:
            path = source / cfg['genesys_datafiles']['output'][key]
            frame = pd.read_csv(path).rename(columns={'Value ': 'Value', 'PathwayScenario': 'Scenario'})
            if 'Scenario' not in frame:
                frame['Scenario'] = frame['Model Version'] if 'Model Version' in frame else cfg['Scenario']
            frame['Scenario'] = frame['Scenario'].map(
                lambda value: next((main for alt, main in names.items() if alt in str(value)), value))
            frame = frame.drop(columns=['Model Version'], errors='ignore')
            data.at[key] = frame
    combined, pieces = run(data, cfg)
    selected = pd.concat([frame for name, frame in pieces if rule_kind(name, all_rules[name]) == kind], ignore_index=True)
    output.mkdir(parents=True, exist_ok=True)

    def export(frame, stem):
        frame = prepare_export(frame, cfg, region_prefix)
        wide = frame.pivot(index=INDEX[:-1], columns='Year', values='Value').reset_index()
        with pd.ExcelWriter(output / (stem + '.xlsx')) as writer:
            wide.to_excel(writer, sheet_name='data', index=False)
        return frame

    if kind == 'inputs':
        result = export(selected, 'inputs_iamc')
    else:
        result = export(combined, 'combined_iamc')
    summary = {'engine': 'GENeSYS-MOD IAMC converter', 'kind': kind,
               'settings': str(settings), 'settings_sha256': hashlib.sha256(settings.read_bytes()).hexdigest(),
               'source': str(source), 'input_file': str(input_file),
               'observations': len(result), 'variables': result.Variable.nunique(),
               'region_prefix': region_prefix,
               'nomenclature_mapping': 'Variable names are defined directly by the conversion profile'}
    return result, summary

"""Provides interface to CIMAGE."""
from ctesi.utils import CimageParams
from copy import deepcopy
from collections import defaultdict, OrderedDict
import config.config as config
import pathlib
import requests
import subprocess


QUANT_PARAMS_PATH = config.SEARCH_PARAMS_PATH.parent.joinpath('quantification')


def quantify(name, dta_link, experiment_type, path, search_params=None, setup_dta=True):
    if setup_dta:
        dta_paths = setup_dta_folders(name, path, dta_link, search_params)
    else:
        dta_paths = _get_dta_paths(path)

    params_path = str(_get_params_path(experiment_type, path, search_params))

    normal_search = cimage(params_path, dta_paths['lh'], name, hl_flag=False)
    inverse_search = cimage(params_path, dta_paths['hl'], name, hl_flag=True)

    if normal_search == 0 and inverse_search == 0:
        return (
            combine(path, experiment_type) == 0 and
            combine(path, experiment_type, dta_folder='dta_HL') == 0
        )
    else:
        return False


def cimage(params_path, dta_folder_path, name, hl_flag):
    if hl_flag:
        name = '{}_HL'.format(name)

    return subprocess.Popen([
        'cimage2',
        params_path,
        name
    ], cwd=dta_folder_path).wait()


def combine(path, experiment_type, dta_folder='dta'):
    args = [
        'cimage_combine',
        'output_rt_10_sn_2.5.to_excel.txt',
        dta_folder
    ]

    if experiment_type is not 'isotop':
        args.insert(1, 'by_protein')

    return subprocess.Popen(args, cwd=str(path)).wait()


def setup_dta_folders(name, path, dta_link, search_params=None):
    # download dta results
    # yes, this is a publicly accessible url. lol.
    r = requests.get(dta_link)
    dta_content = r.text

    if search_params and 'diff_mods' in search_params:
        symbol_mod_map = _symbolify_diff_mods(search_params['diff_mods'])[0]
        for symbol, mods in symbol_mod_map.items():
            for mod in mods:
                dta_content = dta_content.replace('({})'.format(mod['mass']), symbol)

    dta_path = path.joinpath('dta')
    dta_path.mkdir()

    # duplicate dta file for cimage
    dta_hl_path = path.joinpath('dta_HL')
    dta_hl_path.mkdir()

    dta_file_path = dta_path.joinpath('DTASelect-filter_{}_foo.txt'.format(name))

    # write data file to disk for regular L/H cimage run
    with dta_file_path.open('w') as f:
        f.write(dta_content)

    with dta_hl_path.joinpath(dta_file_path.name).open('w') as f:
        f.write(dta_content)

    return {
        'lh': str(dta_path),
        'hl': str(dta_hl_path)
    }


def _get_dta_paths(path):
    return {
        'lh': str(path.joinpath('dta')),
        'hl': str(path.joinpath('dta_HL'))
    }


def _get_params_path(experiment_type, path, search_params=None):
    params_path = QUANT_PARAMS_PATH.joinpath(experiment_type).with_suffix('.params').resolve()

    if search_params and 'diff_mods' in search_params:
        return _make_custom_params(path, params_path, search_params['diff_mods'])
    else:
        return params_path


def _make_custom_params(exp_path, params_path, diff_mods):
    params = CimageParams(str(params_path))

    (symbol_mod_map, diff_mods) = _symbolify_diff_mods(diff_mods)

    for symbol, mods in symbol_mod_map.items():
        for mod in mods:
            row = OrderedDict()
            for atom in params.chem_headers:
                row[atom.upper()] = mod['comp'][atom]
            if mod['light']:
                params.light[mod['symbol']] = row
            if mod['heavy']:
                params.heavy[mod['symbol']] = row

    light_path = exp_path.resolve().joinpath('custom.light')
    heavy_path = exp_path.resolve().joinpath('custom.heavy')
    custom_params_path = exp_path.resolve().joinpath('custom.params')

    params['light.chem.table'] = str(light_path)
    params['heavy.chem.table'] = str(heavy_path)

    params.write_file(str(custom_params_path))
    params.write_chem_tables(light_path=str(light_path), heavy_path=str(heavy_path))

    return custom_params_path


def _symbolify_diff_mods(diff_mods):
    # we're mutating this a lot, better to work on copy
    diff_mods = _degen_annotate_diff_mods(deepcopy(diff_mods))

    diff_symbols = ['*', '#', '@']
    symbols = iter(diff_symbols)
    symbol_mod_map = defaultdict(list)

    for mod in diff_mods:
        # make sure we haven't already paired this one up
        if 'symbol' in mod:
            symbol_mod_map[mod['symbol']].append(mod)
            continue
        try:
            # first we add diff-mods that appear in both light and heavy
            # and then attempt to find a pair
            if mod['light'] and mod['heavy']:
                mod['symbol'] = next(symbols)
            elif mod['light'] or mod['heavy']:
                opposite = 'heavy' if mod['light'] else 'light'
                same = 'light' if mod['light'] else 'heavy'

                # find another diff mod with same isotopically degerate formula
                paired_mod = next((
                    x for x in diff_mods 
                    if 'symbol' not in x
                    and x[opposite]
                    and not x[same]
                    and x['degen'] == mod['degen']
                ), None)

                symbol = next(symbols)

                if paired_mod:
                    paired_mod['symbol'] = symbol

                mod['symbol'] = symbol

            if 'symbol' in mod:
                symbol_mod_map[mod['symbol']].append(mod)
        except StopIteration:
            # we've run out of symbols to hand out...
            break

    return (symbol_mod_map, diff_mods)


def _degen_annotate_diff_mods(diff_mods):
    # group diff mods by chemical formula not taking into account isotopic composition
    # these molecules get the same symbol
    for mod in diff_mods:
        mod['degen'] = deepcopy(mod['comp'])
        mod['degen']['C'] += mod['degen']['C13']
        mod['degen']['H'] += mod['degen']['H2']
        mod['degen']['N'] += mod['degen']['N15']
        del mod['degen']['C13'], mod['degen']['H2'], mod['degen']['N15']

    return diff_mods

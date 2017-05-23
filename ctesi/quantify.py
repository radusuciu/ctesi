"""Provides interface to CIMAGE."""
import config.config as config
import pathlib
import requests
import subprocess


QUANT_PARAMS_PATH = config.SEARCH_PARAMS_PATH.parent.joinpath('quantification')


def quantify(name, dta_link, experiment_type, path):
    dta_paths = setup_dta_folders(name, path, dta_link)
    params_path = str(_get_params_path(experiment_type))

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


def setup_dta_folders(name, path, dta_link):
    # download dta results
    # yes, this is a publicly accessible url. lol.
    r = requests.get(dta_link)
    dta_content = r.text

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


def _get_params_path(experiment_type):
    return QUANT_PARAMS_PATH.joinpath(experiment_type).with_suffix('.params').resolve()

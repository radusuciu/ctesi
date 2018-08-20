from ctesi.core.exceptions import ExperimentTypeSearchParamsMissing, SearchOptionNotCustomizeable
import config.config as config
import pathlib
import json


SEARCH_PARAMS_PATH = pathlib.Path(config.SEARCH_PARAMS_PATH)
EXPERIMENT_TYPES_PATH = SEARCH_PARAMS_PATH.joinpath('experiment_type.json')
BASE_PATH = SEARCH_PARAMS_PATH.joinpath('base.json')


class SearchParams:
    def __init__(self, experiment_type=None, diff_mods=[], options={}):
        self.base = self._get_base()
        self.values = self._get_base_values()
        self._experiment_type = experiment_type

        if experiment_type:
            self._load_experiment_type(experiment_type)

        self.diff_mods = diff_mods
        self.options = options

    @property
    def experiment_type(self):
        return self._experiment_type

    @experiment_type.setter
    def experiment_type(self, experiment_type=None):
        self._experiment_type = experiment_type

        if experiment_type:
            self._load_experiment_type()

    @property
    def diff_mods(self):
        return self._diff_mods

    @diff_mods.setter
    def diff_mods(self, diff_mods=[]):
        self.values['diff_mods'] = ['{} {} '.format(mod['mass'], mod['aa']) for mod in diff_mods]
        self._diff_mods = diff_mods

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, options={}):
        for k, v in options.items():
            if k in self.customizeable_keys:
                self.values[k] = v
            else:
                raise SearchOptionNotCustomizeable

        self._options = options

    @property
    def ip2_dict(self):
        return { self.base[k]['ip2_alias']: v  for k, v in self.values.items() }

    @property
    def customizeable_keys(self):
        return [ k for k in self.base.keys() if k.get('allow_custom') or k.get('require_custom')]
    
    def _load_experiment_type(self):
        with EXPERIMENT_TYPES_PATH.open() as f:
            all_experiment_types = json.loads(f.read())

        if self.experiment_type not in all_experiment_types:
            raise ExperimentTypeSearchParamsMissing

        self.values.update(all_experiment_types[self.experiment_type])

    def _get_base(self):
        with BASE_PATH.open() as f:
            return json.loads(f.read())

    def _get_base_values(self):
        return { k: v['default'] for k, v in self.base.items() }

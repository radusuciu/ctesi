"""Perform search of dataset on IP2."""
from ip2api import IP2
import config.config as config
import pathlib
import json
import time

SEARCH_PARAMS_PATH = pathlib.Path(config.SEARCH_PARAMS_PATH)


class Search:
    """Perform search of dataset on IP2."""

    def __init__(self, name):
        """Initialize Search with dataset name."""
        self.name = name

    def login(self, username, password=None, cookie=None):
        """Login to IP2 and keep reference to session."""
        self._ip2 = IP2(
            ip2_url=config.IP2_URL,
            username=username,
            default_project_name=config.PROJECT_NAME
        )

        if password:
            return self._ip2.login(password)
        elif cookie:
            return self._ip2.cookie_login(cookie)
        else:
            return False


    def search(self, organism, experiment_type, file_paths, status_callback=None, search_params=None):
        """Initiate search on IP2."""
        params = self._get_params(experiment_type, search_params)

        # get database by file name
        database = self._ip2.get_database(self._get_database_path(organism)['name'])

        (experiment, job) = self._ip2.search(
            name=self.name,
            file_paths=file_paths,
            search_options={
                'params': params,
                'database': database
            },
            convert=True,
            monoisotopic=True
        )

        link = self._check_search_status(job, experiment, status_callback)

        return link

    def _get_params(self, experiment_type, search_params=None):
        with SEARCH_PARAMS_PATH.joinpath('search_params.json').open() as f:
            params_map = json.loads(f.read())

        if experiment_type not in params_map:
            raise KeyError('Search params are not available for this experiment type')

        with SEARCH_PARAMS_PATH.joinpath(params_map[experiment_type]).open() as f:
            params = json.loads(f.read())

        if search_params and 'diff_mods' in search_params:
            diff_mods = search_params['diff_mods']
            new_mods = ['{} {} '.format(mod['mass'], mod['aa']) for mod in diff_mods]
            params['sp.diffmods'] = new_mods

        if search_params and 'options' in search_params:
            params = self._add_options_to_params(params, search_params['options'])


        return params

    def _add_options_to_params(self, params, options=None):
        if not options:
            return params

        options_map = {
            'minPeptidesPerProtein': 'dp.p',
            'maxNumDiffmod': 'sp.maxNumDiffmod'
        }

        for option, param_equivalent in options_map.items():
            if option in options:
                params[param_equivalent] = options[option]

        return params

    def _get_database_path(self, organism):
        with SEARCH_PARAMS_PATH.joinpath('databases.json').open() as f:
            database_map = json.loads(f.read())

        if organism not in database_map:
            raise KeyError('There is no database set for this organism')

        return database_map[organism]

    def _check_search_status(self, job, experiment, status_callback=None):
        polling_interval = 180

        # wait a bit before we poll for status
        time.sleep(polling_interval)

        while True:
            start = time.clock()

            try:
                job.status()

                if status_callback:
                    status_callback(job)
            except LookupError:
                # job was not found, the job is finished or something went
                # horribly wrong
                tries = tries + 1

                try:
                    dta_select_link = experiment.get_dtaselect_link()
                    job.finished = True

                    if status_callback:
                        status_callback(job)

                    return dta_select_link
                except:
                    # swallow exception until we've run out of tries
                    if tries >= max_retries:
                        raise
                    else:
                        pass

            work_duration = time.clock() - start
            time.sleep(polling_interval - work_duration)

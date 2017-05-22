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

    def login(self, username, password):
        """Login to IP2 and keep reference to session."""
        self._ip2 = IP2(
            ip2_url=config.IP2_URL,
            username=username,
            default_project_name=config.PROJECT_NAME
        )
        return self._ip2.login(password)

    def search(self, organism, experiment_type, file_paths, status_callback=None):
        """Initiate search on IP2."""
        params = self._get_params(experiment_type)
        # get database by file name
        database = self._ip2.get_database(self._get_database_path(organism)['name'])

        (experiment, job) = self._ip2.search(
            name=self.name,
            file_paths=file_paths,
            search_options={
                'params': params,
                'database': database
            }
        )

        link = self._check_search_status(job, experiment, status_callback)

        return link

    def _get_params(self, experiment_type):
        with SEARCH_PARAMS_PATH.joinpath('search_params.json').open() as f:
            params_map = json.loads(f.read())

        if experiment_type not in params_map:
            raise KeyError('Search params are not available for this experiment type')

        with SEARCH_PARAMS_PATH.joinpath(params_map[experiment_type]).open() as f:
            params = json.loads(f.read())

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
                
                job.finished = True

                if status_callback:
                    status_callback(job)

                return experiment.get_dtaselect_link()

            work_duration = time.clock() - start
            time.sleep(polling_interval - work_duration)

"""Define processing actions for celery task queue."""
from celery import Celery
from .convert import convert
from .quantify import quantify
import ctesi.api as api
import pathlib
import os

celery = Celery('tasks', broker='amqp://guest@rabbitmq//')
celery.conf.update(accept_content=['json', 'pickle'])


@celery.task(serializer='pickle')
def process(data, search, user_id, experiment_id, path):
    # convert .raw to .ms2
    api.update_experiment_status(experiment_id, 'converting')

    # removing first bit of file path since that is the upload folder
    corrected_path = pathlib.PurePath(*path.parts[path.parts.index('users') + 1:])
    convert_status = convert(corrected_path.as_posix())
    converted_paths = [path.joinpath(f) for f in convert_status['files_converted']]

    # initiate IP2 search
    api.update_experiment_status(experiment_id, 'searching')
    dta_select_link = search.search(
        data['organism'],
        data['type'],
        [f for f in converted_paths if f.suffix == '.ms2']
    )

    # run things through cimage
    api.update_experiment_status(experiment_id, 'cimage')
    quantify(data['name'], dta_select_link, data['type'], path)

    # clean up the big files
    for ext in ('*.raw', '*.ms2', '*.mzXML'):
        for f in path.glob(ext):
            os.unlink(str(f))

    api.update_experiment_status(experiment_id, 'done')

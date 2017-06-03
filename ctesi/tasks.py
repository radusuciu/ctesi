"""Define processing actions for celery task queue."""
from celery import Celery
from .convert import convert
from .quantify import quantify
from .search import Search
import ctesi.api as api
import functools
import pathlib
import json
import pickle
import os

celery = Celery('tasks', broker='amqp://guest@rabbitmq//')


@celery.task
def process(user_id, experiment_id, ip2_username, ip2_cookie):
    # convert .raw to .ms2
    # removing first bit of file path since that is the upload folder
    experiment = api.get_raw_experiment(experiment_id)
    user = api.get_user(user_id)
    ip2_cookie = pickle.loads(ip2_cookie)

    path = pathlib.Path(experiment.path)
    corrected_path = pathlib.PurePath(*path.parts[path.parts.index('users') + 1:])

    convert_status = convert(
        corrected_path.as_posix(),
        status_callback=functools.partial(update_conversion_status, experiment_id)
    )

    if not convert_status:
        update_conversion_status(experiment_id, {'step': 'converting', 'status': 'error'})
        return

    converted_paths = [path.joinpath(f) for f in convert_status['files_converted']]

    api.update_experiment_status(experiment_id, 'submitting to ip2')

    search = Search(experiment.name)
    search.login(ip2_username, cookie=ip2_cookie)

    # initiate IP2 search
    dta_select_link = search.search(
        experiment.organism,
        experiment.experiment_type,
        [f for f in converted_paths if f.suffix == '.ms2'],
        status_callback=functools.partial(update_search_status, experiment_id),
        search_params=search_params
    )

    # run things through cimage
    api.update_experiment_status(experiment_id, 'cimage')

    quant_result = quantify(
        experiment.name,
        dta_select_link,
        experiment.experiment_type,
        path,
        json.loads(experiment.search_params)
    )

    # clean up the big files
    if quant_result:
        for ext in ('*.raw', '*.ms2', '*.mzXML'):
            for f in path.glob(ext):
                os.unlink(str(f))

        api.update_experiment_status(experiment_id, 'done')
    else:
        api.update_experiment_status(experiment_id, 'error')


def cancel_task(task_id, terminate=True):
    return celery.control.revoke(task_id, terminate=terminate)


def update_conversion_status(experiment_id, status):
    '''Update status of file conversion operation.
    
    Arguments:
        status {dict} -- Returned from cravatt-rawprocessor
        experiment_id {int} -- Experiment id to perform status update on
    '''

    api.update_experiment_status(experiment_id, {
        'step': 'converting',
        'status': status['status'],
        'progress': status['progress'] or 0
    })


def update_search_status(experiment_id, ip2job):
    '''Update status of IP2 search.
    
    Arguments:
        status {dict} -- Returned from cravatt-rawprocessor
        experiment_id {int} -- Experiment id to perform status update on
    '''

    api.update_experiment_status(experiment_id, {
        'step': 'searching',
        'status': ip2job.info['message'],
        'progress': ip2job.progress * 100 or 0
    })

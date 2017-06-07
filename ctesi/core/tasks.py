"""Define processing actions for celery task queue."""
from collections import OrderedDict
from celery import Celery, chain
from celery.exceptions import TaskError
from ctesi.core.convert import convert
from ctesi.core.quantify import quantify
from ctesi.core.search import Search
import ctesi.api as api
import functools
import pathlib
import json
import pickle
import os

celery = Celery('tasks', broker='amqp://guest@rabbitmq//')
celery.conf.update(accept_content=['json', 'pickle'])


def process(experiment_id, ip2_username, ip2_cookie, from_step='convert'):
    # convert .raw to .ms2
    # removing first bit of file path since that is the upload folder
    experiment = api.get_raw_experiment(experiment_id)

    steps = ['convert', 'search', 'quantify']

    signatures = [
        convert_task.s(experiment_id),
        search_task.s(experiment_id, ip2_username, pickle.loads(ip2_cookie)),
        quantify_task.s(experiment_id),
        on_success.s(experiment_id)
    ]

    result = chain(
        signatures[steps.index(from_step):]
    ).apply_async(link_error=on_error.s(experiment_id))

    return result


@celery.task(serializer='pickle')
def convert_task(experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    path = pathlib.Path(experiment.path)
    corrected_path = pathlib.PurePath(*path.parts[path.parts.index('users') + 1:])

    convert_status = convert(
        corrected_path.as_posix(),
        status_callback=functools.partial(update_conversion_status, experiment_id)
    )

    if not convert_status:
        raise TaskError

    return [path.joinpath(f) for f in convert_status['files_converted']]


@celery.task(serializer='pickle')
def search_task(converted_paths, experiment_id, ip2_username, ip2_cookie):
    experiment = api.get_raw_experiment(experiment_id)
    api.update_experiment_status(experiment_id, 'submitting to ip2')

    search = Search(experiment.name)
    search.login(ip2_username, cookie=ip2_cookie)

    # initiate IP2 search
    dta_select_link = search.search(
        experiment.organism,
        experiment.experiment_type,
        [f for f in converted_paths if f.suffix == '.ms2'],
        status_callback=functools.partial(update_search_status, experiment_id),
        search_params=json.loads(experiment.search_params)
    )

    return dta_select_link


@celery.task(serializer='pickle')
def quantify_task(dta_select_link, experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    path = pathlib.Path(experiment.path)
    api.update_experiment_status(experiment_id, 'cimage')

    ret = quantify(
        experiment.name,
        dta_select_link,
        experiment.experiment_type,
        path,
        json.loads(experiment.search_params)
    )

    if not ret:
        raise TaskError


@celery.task
def on_error(request, exc, traceback, experiment_id):
    api.update_experiment_status(experiment_id, 'error')


@celery.task
def on_success(experiment_id):
    # clean up the big files
    if quant_result:
        for ext in ('*.raw', '*.ms2', '*.mzXML'):
            for f in experiment.path.glob(ext):
                os.unlink(str(f))

    api.update_experiment_status(experiment_id, 'done')


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

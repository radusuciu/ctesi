"""Define processing actions for celery task queue."""
from celery import chain
from celery.exceptions import TaskError
from distutils.dir_util import copy_tree, remove_tree
from ctesi import db, celery
from ctesi.core.convert import convert
from ctesi.core.quantify import quantify
from ctesi.core.search import Search
from ctesi.utils import send_mail
from ctesi.api import update_experiment_status as update_status
import config.config as config
import ctesi.api as api
import pathlib
import json
import pickle
import os


def process(experiment_id, ip2_username, ip2_cookie, temp_path=None, send_email=False, user_id=None, from_step='convert'):
    # convert .raw to .ms2
    # removing first bit of file path since that is the upload folder
    experiment = api.get_raw_experiment(experiment_id)
    steps = ['convert', 'search', 'cimage']

    convert_sig = convert_task.si(experiment_id)
    search_sig = search_task.s(experiment_id, ip2_username, pickle.loads(ip2_cookie))
    quantify_sig = quantify_task.s(experiment_id)

    # ammending signatures where necessary for re-runs
    if from_step == 'search':
        ms2_paths = list(experiment.path.glob('*.ms2'))
        search_sig.args = (ms2_paths,) + search_sig.args

    if from_step == 'cimage':
        dta_link = ''
        quantify_sig.args = (dta_link, ) + quantify_sig.args
        quantify_sig.kwargs['setup_dta'] = False

    signatures = [convert_sig, search_sig, quantify_sig, on_success.s(experiment_id)]

    if temp_path:
        signatures = [move_task.s(experiment_id, )] + signatures

    if send_email and user_id:
        signatures =  signatures + [email_task.si(user_id, experiment_id)]

    result = chain(
        signatures[steps.index(from_step):]
    ).apply_async(link_error=on_error.s(experiment_id), ignore_result=False)

    experiment.task_id = result.id
    db.session.commit()

    return result


@celery.task(serializer='pickle', soft_time_limit=600)
def move_task(experiment_id):
    update_status(experiment_id, 'moving files')
    experiment = api.get_raw_experiment(experiment_id)

    # note that it is not okay to clobber existing files
    experiment.path.mkdir(parents=True, exist_ok=False)
    raw_files = experiment.tmp_path.glob('*.raw')

    for i, filepath in enumerate(sorted(raw_files, key=lambda f: f.stem)):
        # rename raw files to reflect dataset name
        # and adding _INDEX to please cimage
        new_name = '{}_{}.raw'.format(experiment.name, str(i + 1))
        filepath.rename(experiment.path.joinpath(new_name))

    remove_tree(str(experiment.tmp_path))


@celery.task(serializer='pickle', soft_time_limit=1800)
def convert_task(experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    path = pathlib.Path(experiment.path)
    corrected_path = pathlib.PurePath(*path.parts[path.parts.index('users'):])

    convert_status = convert(
        corrected_path.as_posix(),
        status_callback=lambda s: update_status(experiment_id, 'converting', meta=s),
    )

    if not convert_status:
        raise TaskError

    return convert_status


@celery.task(serializer='pickle', soft_time_limit=172800)
def search_task(convert_status, experiment_id, ip2_username, ip2_cookie):
    experiment = api.get_raw_experiment(experiment_id)
    update_status(experiment_id, 'submitting to ip2')
    search = Search('{}_{}'.format(experiment.name, str(experiment_id)))
    search.login(ip2_username, cookie=ip2_cookie)


    # initiate IP2 search
    dta_select_link = search.search(
        experiment.organism,
        experiment.experiment_type,
        list(pathlib.Path(experiment.path).glob('*.raw')),
        status_callback=lambda j: update_status(experiment_id, 'searching', meta={'status': j.info['message'], 'progress': j.progress * 100 or 0 }),
        search_params=json.loads(experiment.search_params)
    )

    return dta_select_link


@celery.task(serializer='pickle', soft_time_limit=21600)
def quantify_task(dta_select_link, experiment_id, setup_dta=True):
    experiment = api.get_raw_experiment(experiment_id)
    path = pathlib.Path(experiment.path)

    update_status(experiment_id, 'cimage')

    ret = quantify(
        experiment.name,
        dta_select_link,
        experiment.experiment_type,
        path,
        json.loads(experiment.search_params),
        setup_dta=setup_dta
    )

    if not ret:
        raise TaskError

    return ret

@celery.task(serializer='pickle', bind=True, soft_time_limit=120)
def email_task(self, user_id, experiment_id):
    experiment = api.get_raw_experiment(experiment_id)
    user = api.get_user(user_id)

    subject = 'Your dataset {} has finished processing'.format(experiment.name)
    body = 'You may copy the dataset from the following path (on avatar): {}/{}/{}'.format(
        '/mnt/ctesi',
        experiment.user.username,
        experiment.name
    )

    try:
        send_mail(user.email, subject, body)
    except Exception as e:
        self.retry(countdown=30, exc=e, max_retries=2)


@celery.task
def on_error(request, exc, traceback, experiment_id):
    update_status(experiment_id, 'error')


@celery.task
def on_success(quant_result, experiment_id):
    experiment = api.get_raw_experiment(experiment_id)

    # clean up the big files
    if quant_result:
        for ext in ('*.raw', '*.RAW', '*.ms2', '*.mzXML', '*/*.mzXML'):
            for f in experiment.path.glob(ext):
                os.unlink(str(f))

    # move to mirror results across network
    finished_path = config.FINISHED_PATH.joinpath(
        experiment.user.username,
        experiment.name
    )

    try:
        remove_tree(str(finished_path))
    except FileNotFoundError:
        pass

    copy_tree(str(experiment.path), str(finished_path), preserve_mode=False, preserve_times=False)

    update_status(experiment_id, 'done')

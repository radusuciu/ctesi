"""Handles uploads of .RAW files."""
from werkzeug import secure_filename
from config.config import INSTANCE_PATH
import pathlib


def upload(files, user_id, name, experiment_id):
    path = pathlib.Path(
        INSTANCE_PATH,
        'tmp',
        str(user_id),
        str(experiment_id)
    )

    name = secure_filename(name)

    path.mkdir(parents=True)

    for i, f in enumerate(sorted(files, key=lambda f: f.filename)):
        # only allow .raw extension
        filename = secure_filename(f.filename)
        filepath = pathlib.PurePath(filename)

        if filepath.suffix.lower() == '.raw':
            # rename raw files to reflect dataset name
            # adding _INDEX to please cimage
            filename = name + '_{}.raw'.format(i + 1)
            f.save(str(path.joinpath(filename)))

    return name, path

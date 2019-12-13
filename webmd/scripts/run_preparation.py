#!/usr/bin/env python3
"""
Run Preparation
"""
import argparse
import os
import shutil
import subprocess
import tempfile
from functools import wraps

import requests

CONTROLLER_HOST = os.environ.get('PROWAVE_CONTROLLER_HOST', 'slurmctld:8000')
BASE_URL = 'http://%s/api/webmd/files' % CONTROLLER_HOST


def temp_directory(func):
    """
    Decorated 함수를 temporary directory에서 수행하도록 하는 데코레이터
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tempdir = tempfile.mkdtemp()
        cwd = os.getcwd()
        try:
            os.chdir(tempdir)
            return func(*args, **kwargs)
        finally:
            os.chdir(cwd)
            shutil.rmtree(tempdir)
    return wrapper


@temp_directory
def main():
    """
    Main
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('trajectory_id', type=int)
    args = parser.parse_args()

    # get cleaned.pdb from controller
    get_url = '%s/%d/model.pdb' % (BASE_URL, args.trajectory_id)
    get_response = requests.get(get_url)
    if get_response.status_code == 200:
        with open('model.pdb', 'wb+') as stream:
            stream.write(get_response.content)

    assert os.path.exists('model.pdb')
    subprocess.check_call([
        '/home/nbcc/prowave_compute/autotleap.py',
        '.',
        '-w',
        'TIP3PBOX'
    ])

    try:
        assert os.path.exists('model.prmtop')
        assert os.path.exists('model.inpcrd')
    except AssertionError:
        log_output = subprocess.check_output(['cat', 'leap.log'])
        print(log_output.decode())

    shutil.move('model.pdb', 'model_solv.pdb')
    for file_to_post in ['model_solv.pdb',
                         'model.prmtop',
                         'model.inpcrd',
                         'leaprc',
                         'leap.log']:
        if os.path.exists(file_to_post):
            post_url = '%s/%d/%s' % (BASE_URL, args.trajectory_id, file_to_post)
            with open(file_to_post, 'rb') as stream:
                post_response = requests.post(
                    post_url,
                    data={'file': file_to_post},
                    files={'file': stream}
                )
            assert post_response.status_code == 201


if __name__ == '__main__':
    main()

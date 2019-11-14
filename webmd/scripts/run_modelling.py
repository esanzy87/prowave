#!/usr/bin/env python3
import argparse
import os
import requests
import shutil
import subprocess
import tempfile


BASE_URL = 'http://172.16.0.30:8000'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id', type=int)
    parser.add_argument('project_id', type=int)
    args = parser.parse_args()

    # create and move to temp directory
    tempdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(tempdir)
        # get cleaned.pdb from controller
        get_url = '%s/api/webmd/users/%d/files/projects/%d/model.pdb' % (BASE_URL, args.user_id, args.project_id)
        get_response = requests.get(get_url)
        if get_response.status_code == 200:
            with open('model.pdb', 'wb+') as f:
                f.write(get_response.content)

        assert os.path.exists('model.pdb')
        subprocess.check_call(['/home/nbcc/prowave_compute/autotleap.py', '.', '-w', 'TIP3PBOX'])
        try:
            assert os.path.exists('model.prmtop')
            assert os.path.exists('model.inpcrd')
        except AssertionError:
            log_output = subprocess.check_output(['cat', 'leap.log'])
            print(log_output.decode())
        shutil.move('model.pdb', 'model_solv.pdb')
        for file_to_post in ['model_solv.pdb', 'model.prmtop', 'model.inpcrd', 'leaprc', 'leap.log']:
            if os.path.exists(file_to_post):
                post_url = '%s/api/webmd/users/%d/files/projects/%d/%s' % (BASE_URL, args.user_id, args.project_id, file_to_post)
                with open(file_to_post, 'rb') as f:
                    post_response = requests.post(post_url, data={'file': file_to_post}, files={'file': f})
                assert post_response.status_code == 201
    # End of execution
    finally:
        os.chdir(cwd)
        shutil.rmtree(tempdir)

#!/home/nbcc/anaconda3/bin/python
"""
sfe.scripts.run
"""
import argparse
import os
import shutil
import subprocess
import tempfile

import requests


CONTROLLER_HOST = os.environ.get('PROWAVE_CONTROLLER_HOST', 'slurmctld:8000')

if __name__ == '__main__':
    BASE_URL = 'http://%s/api/solvation-free-energy/works' % CONTROLLER_HOST
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('work_id', type=int)
    PARSER.add_argument('mode', default='m', choices=['m', 't', 'a', 'x'])
    ARGS = PARSER.parse_args()

    # create and move to temp directory
    TEMPDIR = tempfile.mkdtemp()
    CWD = os.getcwd()
    try:
        os.chdir(TEMPDIR)
        # get cleaned.pdb from controller
        RESP1 = requests.get('%s/%d/files/model/' % (BASE_URL, ARGS.work_id))
        if RESP1.status_code == 200:
            with open('model.pdb', 'wb+') as f:
                f.write(RESP1.content)

        assert os.path.exists('model.pdb')
        subprocess.check_call(['/home/nbcc/prowave_compute/autotleap.py', '.'])
        assert os.path.exists('model.prmtop')
        assert os.path.exists('model.inpcrd')
        subprocess.check_call(['/home/nbcc/prowave_compute/rism3d.py', '.', '-m', ARGS.mode])
        # upload result.json
        for file_to_post in ['model.pdb', 'result.json', 'model.prmtop', 'model.inpcrd',
                             'leaprc', 'leap.log', 'plot.svg']:
            if os.path.exists(file_to_post):
                with open(file_to_post, 'rb') as f:
                    RESP2 = requests.post(
                        '%s/%d/files/' % (BASE_URL, ARGS.work_id),
                        data={'file': file_to_post},
                        files={'file': f}
                    )
                assert RESP2.status_code == 201
    # End of execution
    finally:
        os.chdir(CWD)
        shutil.rmtree(TEMPDIR)

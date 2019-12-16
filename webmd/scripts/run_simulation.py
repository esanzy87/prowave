#!/home/nbcc/anaconda3/bin/python3
"""
run simulation
"""
import argparse
import os
import shutil
import subprocess
import tempfile
from functools import wraps

import requests
import yaml


PROWAVE_API_HOST = os.environ.get('PROWAVE_API_HOST', 'slurmctld:8000')


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


def download_file(base_url, file_path):
    """
    downoload file
    """
    get_response = requests.get('%s/%s' % (base_url, file_path))
    assert get_response.status_code == 200

    base_dir = os.path.dirname(file_path)
    if base_dir:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'wb+') as stream:
        stream.write(get_response.content)
        return get_response.content


def upload_file(base_url, file_path):
    """
    upload file
    """
    with open(file_path, 'rb') as stream:
        post_response = requests.post(
            '%s/%s' % (base_url, file_path),
            data={'file': file_path},
            files={'file': stream}
        )
        assert post_response.status_code == 201


@temp_directory
def main():
    """
    main
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('trajectory_id', type=int)
    parser.add_argument('method', choices=['min', 'eq', 'md'])
    parser.add_argument('index', type=int)
    args = parser.parse_args()

    base_url = 'http://{host}/api/webmd/files/{trajectory_id}'.format(
        host=PROWAVE_API_HOST,
        trajectory_id=args.trajectory_id
    )

    download_file(base_url, 'simulations.yml')
    assert os.path.exists('simulations.yml')

    with open('simulations.yml', 'r') as stream:
        simulations = yaml.load(stream, Loader=yaml.Loader)

    assert args.method in simulations
    assert len(simulations[args.method]) > args.index
    simulation = simulations[args.method][args.index]
    download_file(base_url, 'model.prmtop')

    assert 'reference' in simulation
    download_file(base_url, simulation['reference'])

    assert 'basename' in simulation
    basename = simulation['basename']
    state_file = '%s.npz' % basename
    out_file = '%s.out' % basename
    pdb_file = '%s.pdb' % basename
    traj_file = '%s.dcd' % basename
    os.makedirs(os.path.dirname(basename))

    cmd = [
        '/home/nbcc/prowave_compute/simulation.py',
        args.method,
        simulation['reference']
    ]

    if args.method == 'min':
        assert 'maxcyc' in simulation
        cmd.extend([
            str(simulation['maxcyc']),
            '-t', 'model.prmtop',
            '-s', state_file,
        ])

    elif args.method == 'eq':
        assert 'nstlim' in simulation
        cmd.extend([
            str(simulation['nstlim']),
            '-t', 'model.prmtop',
            '-s', state_file,
            '-o', out_file,
        ])

    else:
        assert 'nstlim' in simulation
        cmd.extend([
            str(simulation['nstlim']),
            '-t', 'model.prmtop',
            '-s', state_file,
            '-o', out_file,
            '-T', traj_file,
        ])

    for key, value in simulation.items():
        if key in ('restraint_weight',
                   'dt',
                   'temp0',
                   'tempi',
                   'ntb',
                   'pres0',
                   'ntpr',
                   'ntwx',
                   'cutoff'):
            cmd.extend(['--%s' % key, str(value)])

    subprocess.check_call(cmd)

    for file_to_upload in (state_file, pdb_file, out_file, traj_file):
        if os.path.exists(file_to_upload):
            upload_file(base_url, file_to_upload)


if __name__ == '__main__':
    main()

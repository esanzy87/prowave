#!/usr/bin/env python3
import argparse
import os
import requests
import shutil
import subprocess
import tempfile
import yaml


PROWAVE_API_HOST = os.environ.get('PROWAVE_API_HOST', 'http://172.16.0.30:8000')


def download_file(url):
    get_response = requests.get(url)
    if get_response.status_code == 200:
        with open(url.split('/')[-1], 'wb+') as f:
            f.write(get_response.content)


def upload_file(url):
    file_to_upload = url.split('/')[-1]
    with open(file_to_upload, 'rb') as f:
        post_response = requests.post(url, data={'file': file_to_upload}, files={'file': f})
        assert post_response.status_code == 201


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id', type=int)
    parser.add_argument('project_seq', type=int)
    parser.add_argument('trajectory_seq', type=int)
    parser.add_argument('method', choices=['min', 'eq', 'md'])
    parser.add_argument('index', type=int)
    args = parser.parse_args()

    BASE_URL = '{host}/api/webmd/users/{user_id}/files/projects/{project_seq}/trajectories/{trajectory_seq}'.format(
        host=PROWAVE_API_HOST,
        user_id=args.user_id,
        project_seq=args.project_seq,
        trajectory_seq=args.trajectory_seq
    )

    tempdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(tempdir)
        simulations_yml_get_url = "{base_url}/simulations.yml".format(base_url=BASE_URL)
        download_file(simulations_yml_get_url)
        assert os.path.exists('simulations.yml')
        with open('simulations.yml', 'r') as stream:
            simulations = yaml.load(stream)
            assert args.method in simulations and len(simulations[args.method]) > args.index
            simulation = simulations[args.method][args.index]

        assert args.method in ('min', 'eq', 'md')
        download_file("{base_url}/../../model.prmtop".format(base_url=BASE_URL))
        assert 'reference' in simulation and 'state_file' in simulation
        download_file("{base_url}/{reference}".format(base_url=BASE_URL, reference=simulation['reference']))
        cmd = ['/home/nbcc/prowave_compute/simulation.py', args.method, simulation['reference'].split('/')[-1]]
        if args.method == 'min':
            assert 'maxcyc' in simulation and 'state_file' in simulation
            cmd.extend([
                str(simulation['maxcyc']),
                '-t', 'model.prmtop',
                '-s', simulation['state_file'].split('/')[-1],
            ])
        elif args.method == 'eq':
            assert 'nstlim' in simulation and 'state_file' in simulation and 'out_file' in simulation
            cmd.extend([
                str(simulation['nstlim']),
                '-t', 'model.prmtop',
                '-s', simulation['state_file'].split('/')[-1],
                '-o', simulation['out_file'].split('/')[-1],
            ])
        else:
            assert 'nstlim' in simulation and 'state_file' in simulation and 'out_file' in simulation and 'traj_file' in simulation
            cmd.extend([
                str(simulation['nstlim']),
                '-t', 'model.prmtop',
                '-s', simulation['state_file'].split('/')[-1],
                '-o', simulation['out_file'].split('/')[-1],
                '-T', simulation['traj_file'].split('/')[-1],
            ])

        for key, value in simulation.items():
            if key in ('restraint_weight', 'dt', 'temp0', 'tempi', 'ntb', 'pres0', 'ntpr', 'ntwx', 'cutoff'):
                cmd.extend(['--%s' % key, str(value)])

        subprocess.check_call(cmd)

        upload_file("{base_url}/{file}".format(base_url=BASE_URL, file=simulation['state_file']))
        upload_file("{base_url}/{file}".format(base_url=BASE_URL, file='%s.pdb' % simulation['state_file'].split('.')[0]))
        if 'out_file' in simulation:
            upload_file("{base_url}/{file}".format(base_url=BASE_URL, file=simulation['out_file']))
        if 'traj_file' in simulation:
            upload_file("{base_url}/{file}".format(base_url=BASE_URL, file=simulation['traj_file']))

    # End of execution
    finally:
        os.chdir(cwd)
        shutil.rmtree(tempdir)

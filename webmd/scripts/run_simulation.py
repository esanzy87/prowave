#!/home/nbcc/anaconda3/bin/python3
"""
run simulation
"""
import argparse
import os
import shutil
import subprocess
import tempfile
import requests
import yaml


PROWAVE_API_HOST = os.environ.get('PROWAVE_API_HOST', 'slurmctld:8000')
BASE_URL = 'http://{host}/api/webmd/users'.format(host=PROWAVE_API_HOST)


def download_file(url):
    """
    downoload file
    """
    get_response = requests.get(url)
    if get_response.status_code == 200:
        with open(url.split('/')[-1], 'wb+') as stream:
            stream.write(get_response.content)
            return get_response.content
    return None


def upload_file(url):
    """
    upload file
    """
    file_to_upload = url.split('/')[-1]
    with open(file_to_upload, 'rb') as stream:
        post_response = requests.post(
            url,
            data={'file': file_to_upload},
            files={'file': stream}
        )
        assert post_response.status_code == 201


def main():
    """
    main
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('user_id', type=int)
    parser.add_argument('trajectory_id', type=int)
    parser.add_argument('method', choices=['min', 'eq', 'md'])
    parser.add_argument('index', type=int)
    args = parser.parse_args()

    base_url = '{base}/{user_id}/files/trajectories/{trajectory_id}'.format(
        base=BASE_URL,
        user_id=args.user_id,
        trajectory_id=args.trajectory_id
    )

    tempdir = tempfile.mkdtemp()
    cwd = os.getcwd()
    try:
        os.chdir(tempdir)
        simulations_yml_get_url = "{base_url}/simulations.yml".format(
            base_url=base_url
        )
        download_file(simulations_yml_get_url)
        assert os.path.exists('simulations.yml')

        with open('simulations.yml', 'r') as stream:
            simulations = yaml.load(stream)

        assert args.method in simulations
        assert len(simulations[args.method]) > args.index
        simulation = simulations[args.method][args.index]
        download_file("{base_url}/model.prmtop".format(base_url=base_url))

        assert 'reference' in simulation
        assert 'basename' in simulation
        basename = simulation['basename']
        state_file = '%s.npz' % basename
        out_file = '%s.out' % basename
        pdb_file = '%s.pdb' % basename
        traj_file = '%s.dcd' % basename

        download_file("{base_url}/{reference}".format(
            base_url=base_url,
            reference=simulation['reference'])
        )

        cmd = [
            '/home/nbcc/prowave_compute/simulation.py',
            args.method,
            simulation['reference'].split('/')[-1]
        ]

        if args.method == 'min':
            assert 'maxcyc' in simulation
            cmd.extend([
                str(simulation['maxcyc']),
                '-t', 'model.prmtop',
                '-s', state_file.split('/')[-1],
            ])

        elif args.method == 'eq':
            assert 'nstlim' in simulation
            cmd.extend([
                str(simulation['nstlim']),
                '-t', 'model.prmtop',
                '-s', state_file.split('/')[-1],
                '-o', out_file.split('/')[-1],
            ])

        else:
            assert 'nstlim' in simulation
            cmd.extend([
                str(simulation['nstlim']),
                '-t', 'model.prmtop',
                '-s', state_file.split('/')[-1],
                '-o', out_file.split('/')[-1],
                '-T', traj_file.split('/')[-1],
            ])

        simulation_params = (
            'restraint_weight', 'dt', 'temp0', 'tempi', 'ntb',
            'pres0', 'ntpr', 'ntwx', 'cutoff'
        )
        for key, value in simulation.items():
            if key in simulation_params:
                cmd.extend(['--%s' % key, str(value)])

        subprocess.check_call(cmd)

        for file_to_upload in (state_file, pdb_file, out_file, traj_file):
            if os.path.exists(file_to_upload.split('/')[-1]):
                upload_file("{base_url}/{file}".format(
                    base_url=base_url,
                    file=file_to_upload
                ))

    # End of execution
    finally:
        os.chdir(cwd)
        shutil.rmtree(tempdir)

if __name__ == '__main__':
    main()

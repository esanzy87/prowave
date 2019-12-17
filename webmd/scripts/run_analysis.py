#!/home/nbcc/anaconda3/envs/prowave_compute/bin/python
"""
Run Analysis Script

2019. 12. 16.  Junwon Lee
junwon.lee@sookmyung.ac.kr
"""
import argparse
import os
import shutil
import tempfile
from functools import wraps

import mdtraj as mdt
import numpy as np
import requests


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


def rmsd(ref, trajs):
    """
    Root Mean Square Deviation
    """
    sel = ref.topology.select('protein and name CA')
    trajs.image_molecules(inplace=True)
    trajs.center_coordinates(mass_weighted=True)
    trajs.superpose(ref, frame=0, atom_indices=sel)
    rmsds = mdt.rmsd(trajs, ref, atom_indices=sel, precentered=True) * 10.0
    with open('rmsd.out', 'w') as stream:
        stream.write('# RMSD \n')
        for val in rmsds:
            stream.write('%.4f\n' % val)
    return 'rmsd.out'


def rmsf(ref, trajs):
    """
    Root Mean Square Fluctuation
    """
    sel = ref.topology.select('protein and name CA')
    trajs.image_molecules(inplace=True)
    trajs.center_coordinates(mass_weighted=False)
    trajs.superpose(ref, frame=0, atom_indices=sel)
    coords = [trajs.xyz[:, sel, :]]
    xyz = np.concatenate(coords, axis=0)
    refxyz = np.mean(ref.xyz[:, sel, :], axis=0)
    rmsfs = np.sqrt(3.0 * np.mean((xyz - refxyz) ** 2, axis=(0, 2))) * 10.0  # nm to Angstrom
    atoms = list(ref.topology.subset(sel).to_openmm().atoms())
    with open('rmsf.out', 'w') as stream:
        stream.write('# RMSF\n')
        for i in range(len(sel)):
            resnum = atoms[i].residue.id
            stream.write('{:6s} {:.4f}\n'.format(resnum, rmsfs[i]))
    return 'rmsf.out'


def radgyr(ref, trajs, mass_weighted=True):
    """
    Radius of Gyration
    """
    sel = ref.topology.select('protein')
    if mass_weighted:
        masses = np.array([atom.element.masses for atom in ref.topology.atoms])[sel]
    else:
        masses = np.ones(sel.size)

    weights = masses / masses.sum()
    with open('analyses/radgyr.out', 'w') as stream:
        stream.write('# radgyr')
        for frame in trajs:
            xyz = frame.xyz[:, sel, :]
            centered = (xyz.transpose((1, 0, 2)) - xyz.mean(1)).transpose((1, 0, 2))
            squared_dists = (centered ** 2).sum(2)
            stream.write('%.4f\n' % ((squared_dists * weights).sum(1) ** 0.5 * 10.0))  # nm to Angstrom
    return 'radgyr.out'


def sasa(ref, trajs):
    """
    Solvent Accessible Surface Area
    """
    sel = ref.topology.select('protein')
    trajs.image_molecules(inplace=True)
    trajs.center_coordinates(mass_weighted=False)
    trajs.superpose(ref, frame=0, atom_indices=sel)
    with open('sasa.out', 'w') as stream:
        stream.write('# sasa\n')
        # stream.write('%.4f\n' % mdt.shrake_rupley(ref).sum(axis=1))
        for frame in trajs:
            stream.write('%.4f\n' % mdt.shrake_rupley(frame).sum(axis=1))
    return 'sasa.out'


@temp_directory
def main():
    """
    MAIN
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('trajectory_id', type=int)
    parser.add_argument('method', choices=('rmsd', 'rmsf', 'radgyr', 'sasa'))
    parser.add_argument('md_index', type=int)
    args = parser.parse_args()

    base_url = 'http://{host}/api/webmd/files/{trajectory_id}'.format(
        host=PROWAVE_API_HOST,
        trajectory_id=args.trajectory_id
    )
    md_index = args.md_index + 1
    os.makedirs('md')
    for target_file in ('model.prmtop', 'model.inpcrd', 'md/md%d.dcd' % md_index):
        reseponse = requests.get('%s/%s' % (base_url, target_file))
        assert reseponse.status_code == 200
        with open(target_file, 'wb') as stream:
            stream.write(reseponse.content)

    ref = mdt.load('model.inpcrd', top='model.prmtop')
    trajs = mdt.load('md/md%d.dcd' % md_index, top='model.prmtop')

    if args.method == 'rmsd':
        out_file = rmsd(ref, trajs)
    elif args.method == 'rmsf':
        out_file = rmsf(ref, trajs)
    elif args.method == 'radgyr':
        out_file = radgyr(ref, trajs)
    elif args.method == 'sasa':
        out_file = sasa(ref, trajs)

    with open(out_file, 'r') as stream:
        requests.post(
            '%s/analyses/%s%d.out' % (base_url, args.method, md_index),
            data={'file': out_file},
            files={'file': stream},
        )


if __name__ == '__main__':
    main()

"""
Radius of Gyration 계산 script

2019. 12. 16.  Junwon Lee
junwon.lee@sookmyung.ac.kr
"""
#!/home/nbcc/anaconda3/bin/python
import os
import numpy as np
import mdtraj as mdt


def get_masses(topology):
    """
    get mass of each atom

    :param topology:
    :return:
    """
    masses = []
    for atom in topology.atoms:
        masses.append(atom.element.mass)
    return np.array(masses)


def compute_rg(frame, sel, mass_weighted):
    """
    Calculate Radius of Gyration for single frame
    """
    num_atoms = sel.size
    if mass_weighted:
        masses = get_masses(frame.topology)[sel]
    else:
        masses = np.ones(num_atoms)

    xyz = frame.xyz[:, sel, :]
    weights = masses / masses.sum()

    mu = xyz.mean(1)
    centered = (xyz.transpose((1, 0, 2)) - mu).transpose((1, 0, 2))
    squared_dists = (centered ** 2).sum(2)
    return (squared_dists * weights).sum(1) ** 0.5 * 10.0  # nm to Angstrom


def main():
    """
    RadGyr
    """
    cwd = os.getcwd()

    try:
        os.chdir('data/webmd_data/6')
        ref = mdt.load('model.inpcrd', top='model.prmtop')
        sel = ref.topology.select('protein')
        trajs = mdt.load('md/md1.dcd', top='model.prmtop')
        trajs.image_molecules(inplace=True)
        trajs.center_coordinates(mass_weighted=True)
        trajs.superpose(ref, frame=0, atom_indices=sel)

        with open('analyses/radgyr.out', 'w') as stream:
            stream.write('# radgyr')
            stream.write('0.0')
            for t in trajs:
                stream.write('%.4f\n' % compute_rg(t, sel, False))
    finally:
        os.chdir(cwd)


if __name__ == '__main__':
    main()

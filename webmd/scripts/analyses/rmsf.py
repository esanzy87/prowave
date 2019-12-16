"""
Root Mean Square Fluctuation 계산 script

2019. 12. 16.  Junwon Lee
junwon.lee@sookmyung.ac.kr
"""
#!/home/nbcc/anaconda3/bin/python
import os
import numpy as np
import mdtraj as mdt


def main():
    """
    RMSF
    """
    cwd = os.getcwd()

    try:
        os.chdir('data/webmd_data/6')
        ref = mdt.load('model.inpcrd', top='model.prmtop')
        sel = ref.topology.select('protein and name CA')

        coords = []        
        trajs = mdt.load('md/md1.dcd', top='model.prmtop')
        trajs.image_molecules(inplace=True)
        trajs.center_coordinates(mass_weighted=False)
        trajs.superpose(ref, frame=0, atom_indices=sel)

        tsel = trajs.xyz[:, sel, :]
        coords.append(tsel)

        xyz = np.concatenate(coords, axis=0)
        refxyz = np.mean(ref.xyz[:, sel, :], axis=0)

        rmsf = np.sqrt(3.0 * np.mean((xyz - refxyz) ** 2, axis=(0, 2))) * 10.0  # nm to Angstrom

        atoms = list(ref.topology.subset(sel).to_openmm().atoms())

        with open('analyses/rmsf.out', 'w') as stream:
            stream.write('# RMSF\n')
            for i in range(len(sel)):
                resnum = atoms[i].residue.id
                stream.write('{:6s} {:.4f}\n'.format(resnum, rmsf[i]))
    finally:
        os.chdir(cwd)


if __name__ == '__main__':
    main()

"""
Root Mean Square Deviation 계산 script

2019. 12. 16.  Junwon Lee
junwon.lee@sookmyung.ac.kr
"""
#!/home/nbcc/anaconda3/bin/python
import os
import mdtraj as mdt


def main():
    """
    RMSD
    """
    cwd = os.getcwd()

    try:
        os.chdir('data/webmd_data/6')
        ref = mdt.load('model.inpcrd', top='model.prmtop')
        sel = ref.topology.select('protein and name CA')
        trajs = mdt.load('md/md1.dcd', top='model.prmtop')
        trajs.image_molecules(inplace=True)
        trajs.center_coordinates(mass_weighted=True)
        trajs.superpose(ref, frame=0, atom_indices=sel)
        rmsds = mdt.rmsd(trajs, ref, atom_indices=sel, precentered=True) * 10.0

        with open('md/rmsd.out', 'w') as stream:
            stream.write('# RMSD \n')
            stream.write('0.0\n')
            for val in rmsds:
                stream.write('%.4f\n' % val)
    finally:
        os.chdir(cwd)


if __name__ == '__main__':
    main()

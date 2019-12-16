"""
RMSD 계산 script
"""
#!/home/nbcc/anaconda3/bin/python
import os
import mdtraj as mdt


def main():
    """
    RMSD
    """
    cwd = os.getcwd()
    # base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    # base_dir = os.path.join(base_dir, 'data', 'webmd_data', '6')
    try:
        os.chdir('data/webmd_data/6')
        r = mdt.load('model.inpcrd', top='model.prmtop')
        sel = r.topology.select('protein and name CA')

        with open('md/rmsd.out', 'w') as stream:
            stream.write('# rmsd \n')
            stream.write('0.0\n')
            t = mdt.load('md/md1.dcd', top='model.prmtop')
            t.image_molecules(inplace=True)
            t.center_coordinates(mass_weighted=True)
            t.superpose(r, frame=0, atom_indices=sel)
            rmsds = mdt.rmsd(t, r, atom_indices=sel, precentered=True) * 10.0

            for val in rmsds:
                stream.write('%.4f\n' % val)
    finally:
        os.chdir(cwd)


if __name__ == '__main__':
    main()

"""
Solvent Accesible Surface Area 계산 Script

2019. 12. 16.  Junwon Lee
junwon.lee@sookmyung.ac.kr
"""
#!/home/nbcc/anaconda3/bin/python
import os
import mdtraj as mdt


def main():
    """
    SASA
    """
    cwd = os.getcwd()

    try:
        os.chdir('data/webmd_data/6')
        ref = mdt.load('model.inpcrd', top='model.prmtop')
        sel = ref.topology.select('protein')
        trajs = mdt.load('md/md1.dcd', top='model.prmtop')
        trajs.image_molecules(inplace=True)
        trajs.center_coordinates(mass_weighted=False)
        trajs.superpose(ref, frame=0, atom_indices=sel)
        with open('analyses/rmsf.out', 'w') as stream:
            stream.write('# sasa\n')
            stream.write('%.4f\n' % mdt.shrake_rupley(ref).sum(axis=1))
            for frame in trajs:
                stream.write('%.4f\n' % mdt.shrake_rupley(frame).sum(axis=1))
    finally:
        os.chdir(cwd)


if __name__ == '__main__':
    main()

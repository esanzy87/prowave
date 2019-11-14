"""
pdbutil.py
"""
import argparse


RESSOLV = (
    'WAT', 'HOH', 'AG', 'AL', 'Ag', 'BA', 'BR', 'Be', 'CA', 'CD', 'CE',
    'CL', 'CO', 'CR', 'CS', 'CU', 'CU1', 'Ce', 'Cl-', 'Cr', 'Dy', 'EU',
    'EU3', 'Er', 'F', 'FE', 'FE2', 'GD3', 'HE+', 'HG', 'HZ+', 'Hf',
    'IN', 'IOD', 'K', 'K+', 'LA', 'LI', 'LU', 'MG', 'MN', 'NA', 'NH4',
    'NI', 'Na+', 'Nd', 'PB', 'PD', 'PR', 'PT', 'Pu', 'RB', 'Ra', 'SM',
    'SR', 'Sm', 'Sn', 'SO4', 'TB', 'TL', 'Th', 'Tl', 'Tm', 'U4+', 'V2+', 'Y',
    'YB2', 'ZN', 'Zr'
)
RESNA = ('C', 'G', 'U', 'A', 'DC', 'DG', 'DT', 'DA')
RESPROT = {
    'ALA': 'A',
    'ARG': 'R',
    'ASN': 'N',
    'ASP': 'D',
    'CYS': 'C',
    'GLN': 'Q',
    'GLU': 'E',
    'GLY': 'G',
    'HIS': 'H',
    'ILE': 'I',
    'LEU': 'L',
    'LYS': 'K',
    'MET': 'M',
    'PHE': 'F',
    'PRO': 'P',
    'SER': 'S',
    'THR': 'T',
    'TRP': 'W',
    'TYR': 'Y',
    'VAL': 'V',
}
NON_STANDARD = {
    'SEP': 'SER',
    'TPO': 'THR',
    'PTR': 'TYR',
    'PDS': 'ASP',
    'PHL': 'ASP',
    'MLY': 'LYS',
    'CSP': 'CYS',
    'MSE': 'MET',
    'GMA': 'GLU',
    'OCS': 'CYS',
    'CYX': 'CYS',
    'UNK': 'GLY',
}
PROTONATION_STATES = ['HIS', 'HIE', 'HID', 'HIP', 'HIN']
AA_ATOMS = {
    'ALA': ('N', 'H', 'CA', 'HA', 'CB', 'HB1', 'HB2', 'HB3', 'C', 'O'),
    'ARG': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'HD2', 'HD3', 'NE', 'HE', 'CZ',
            'NH1', 'HH11', 'HH12', 'NH2', 'HH21', 'HH22', 'C', 'O'),
    'ASH': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'OD1', 'OD2', 'HD2', 'C', 'O'),
    'ASN': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'OD1', 'ND2', 'HD21', 'HD22', 'C', 'O'),
    'ASP': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'OD1', 'OD2', 'C', 'O'),
    'CYM': ('N', 'H', 'CA', 'HA', 'CB', 'HB3', 'HB2', 'SG', 'C', 'O'),
    'CYS': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'SG', 'HG', 'C', 'O'),
    'CYX': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'SG', 'C', 'O'),
    'GLH': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'OE1', 'OE2', 'HE2', 'C', 'O'),
    'GLN': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'OE1', 'NE2', 'HE21', 'HE22', 'C', 'O'),
    'GLU': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'OE1', 'OE2', 'C', 'O'),
    'GLY': ('N', 'H', 'CA', 'HA2', 'HA3', 'C', 'O'),
    'HID': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'ND1', 'HD1', 'CE1', 'HE1', 'NE2', 'CD2', 'HD2', 'C', 'O'),
    'HIE': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'ND1', 'CE1', 'HE1', 'NE2', 'HE2', 'CD2', 'HD2', 'C', 'O'),
    'HIP': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'ND1', 'HD1', 'CE1', 'HE1', 'NE2', 'HE2', 'CD2', 'HD2',
            'C', 'O'),
    'HYP': ('N', 'CD', 'HD22', 'HD23', 'CG', 'HG', 'OD1', 'HD1', 'CB', 'HB2', 'HB3', 'CA', 'HA', 'C', 'O'),
    'ILE': ('N', 'H', 'CA', 'HA', 'CB', 'HB', 'CG2', 'HG21', 'HG22', 'HG23', 'CG1', 'HG12', 'HG13', 'CD1', 'HD11',
            'HD12', 'HD13', 'C', 'O'),
    'LEU': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG', 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22',
            'HD23', 'C', 'O'),
    'LYN': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'HD2', 'HD3', 'CE', 'HE2', 'HE3', 'NZ',
            'HZ2', 'HZ3', 'C', 'O'),
    'LYS': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'CD', 'HD2', 'HD3', 'CE', 'HE2', 'HE3', 'NZ',
            'HZ1', 'HZ2', 'HZ3', 'C', 'O'),
    'MET': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'HG2', 'HG3', 'SD', 'CE', 'HE1', 'HE2', 'HE3', 'C', 'O'),
    'PHE': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'CD1', 'HD1', 'CE1', 'HE1', 'CZ', 'HZ', 'CE2', 'HE2', 'CD2',
            'HD2', 'C', 'O'),
    'PRO': ('N', 'CD', 'HD2', 'HD3', 'CG', 'HG2', 'HG3', 'CB', 'HB2', 'HB3', 'CA', 'HA', 'C', 'O'),
    'SER': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'OG', 'HG', 'C', 'O'),
    'THR': ('N', 'H', 'CA', 'HA', 'CB', 'HB', 'CG2', 'HG21', 'HG22', 'HG23', 'OG1', 'HG1', 'C', 'O'),
    'TRP': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'CD1', 'HD1', 'NE1', 'HE1', 'CE2', 'CZ2', 'HZ2', 'CH2',
            'HH2', 'CZ3', 'HZ3', 'CE3', 'HE3', 'CD2', 'C', 'O'),
    'TYR': ('N', 'H', 'CA', 'HA', 'CB', 'HB2', 'HB3', 'CG', 'CD1', 'HD1', 'CE1', 'HE1', 'CZ', 'OH', 'HH', 'CE2',
            'HE2', 'CD2', 'HD2', 'C', 'O'),
    'VAL': ('N', 'H', 'CA', 'HA', 'CB', 'HB', 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23', 'C', 'O'),
}


def find_disulfid_bond_candidate(atoms):
    from scipy.spatial import distance
    pass


class Atom:
    def __init__(self, line):
        self.record = line[0:6]
        self.id = line[6:11].strip()
        self.name = line[12:16].strip()
        self.altloc = line[16].strip()
        self.resname = line[17:20]
        self.chain = line[21].strip()
        self.resnum = line[22:26].strip()
        self.icode = line[26].strip()
        self.x = line[30:38].strip()
        self.y = line[38:46].strip()
        self.z = line[46:54].strip()
        self.occ = line[54:60].strip()
        self.temp = line[60:66].strip()
        self.segid = line[72:76].strip()
        self.elem = line[76:78].strip()
        self.charge = line[78:80].strip()

    def serialize(self):
        return {
            "record": self.record,
            "id": self.id,
            "name": self.name,
            "altloc": self.altloc,
            "resname": self.resname,
            "chain": self.chain,
            "resnum": self.resnum,
            "icode": self.icode,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "occ": self.occ,
            "temp": self.temp,
            "elem": self.elem,
            "charge": self.charge
        }

    def deserialize(self):
        return "%-6s%5s %-4s%1s%3s %1s%4s%1s   %8s%8s%8s%6s%6s      %-4s%2s%3s" % (
            self.record, self.id, self.name, self.altloc, self.resname, self.chain,
            self.resnum, self.icode, self.x, self.y, self.z, self.occ, self.temp,
            self.segid, self.elem, self.charge
        )


class Model:
    def __init__(self, lines):
        self.atoms = list()
        for line in lines:
            record = line[0:6]
            assert record in ('ATOM  ', 'HETATM', 'TER   ')
            self.atoms.append(Atom(line))

    @property
    def chains(self):
        _chains = set()
        for atom in self.atoms:
            _chains.add(atom.chain)
        return list(_chains)

    @property
    def residues(self):
        _residues = set()
        for atom in self.atoms:
            _residues.add((atom.chain, atom.resnum, atom.resname))
        return list(_residues)

    @property
    def non_standards(self):
        return {_residue for _residue in self.residues if _residue[2] in NON_STANDARD}

    @property
    def disulfide_bond_candidates(self):
        import numpy as np
        from scipy.spatial import distance
        cutoff = 3.0
        _ret = []
        for chain in self.chains:
            _sg_atoms = []
            for atom in self.atoms:
                if atom.chain != chain:
                    continue

                if not atom.name == 'SG' or atom.resname not in ('CYS', 'CYX', 'CYM'):
                    continue

                _sg_atoms.append(atom)

            if not _sg_atoms:
                continue

            coords = np.array([(a.x, a.y, a.z) for a in _sg_atoms])
            dist = distance.pdist(coords, metric='euclidean')
            idist = 0
            for i, iatm in enumerate(_sg_atoms):
                for j, jatm in enumerate(_sg_atoms):
                    if i >= j:
                        continue
                    d = dist[idist]
                    idist += 1
                    if d >= cutoff:
                        continue
                    record_i = (iatm.id, chain, iatm.resnum, iatm.resname)
                    record_j = (jatm.id, chain, jatm.resnum, jatm.resname)
                    _ret.append((record_i, record_j, d))
        return _ret

    @property
    def protonation_states(self):
        return {_residue for _residue in self.residues if _residue[2] in PROTONATION_STATES}

    @property
    def solvent_ions(self):
        return {(_residue[0], _residue[2]) for _residue in self.residues if _residue[2] in RESSOLV}

    @property
    def nucleotides(self):
        return {_residue for _residue in self.residues if _residue[2] in RESNA}


class Topology:
    def __init__(self, stream):
        stream.seek(0)
        self.models = []
        self.seqres = dict()
        acc = []
        for line in stream:
            record = line[0:6]
            if record in ('ATOM  ', 'HETATM', 'TER   '):
                acc.append(line)
                continue

            if record == 'ENDMDL':
                self.models.append(Model(acc))
                acc = []
                continue

            if record == 'SEQRES':
                chain = line[11]
                if chain not in self.seqres:
                    self.seqres[chain] = []
                self.seqres[chain].extend(line[19:].strip().split())
                continue

        # 모델이 1개밖에 없는 경우에는 ENDMDL 이 나타나지 않기 때문에 아래가 필요함
        if acc:
            self.models.append(Model(acc))

    @property
    def chains(self):
        return list(self.seqres.keys())

    @property
    def sequence(self):
        _sequences = []
        for chain, residues in self.seqres.items():
            _residues = []
            for residue in residues:
                if residue in RESPROT:
                    _residues.append(RESPROT[residue])
                elif residue in NON_STANDARD:
                    _residues.append(RESPROT[NON_STANDARD[residue]])
            _sequences.append(''.join(_residues))
        return ' '.join(_sequences)

    @property
    def non_standards(self):
        return sorted(list(self.models[0].non_standards))

    @property
    def protonation_states(self):
        return sorted(list(self.models[0].protonation_states))

    @property
    def disulfide_bond_candidates(self):
        return self.models[0].disulfide_bond_candidates

    @property
    def solvent_ions(self):
        return sorted(list(self.models[0].solvent_ions))

    def select_model(self, index):
        """
        PDB의 파일 스트림 또는 StringIO 스트림에서
        지정한 model_index의 model을 추출하여 StringIO 스트림을 반환함

        :param index: 추출하고자 하는 model의 index, 0부터 시작하며 기본값은 0
        """
        self.models = [self.models[index]]

    def select_chains(self, chain_ids):
        """
        모델이 1개인 PDB파일의 파일 스트림 또는 StringIO 스트림에서
        chain_ids 지정한 1개 또는 그 이상의 chain을 추출하여 StringIO 스트림을 반환함

        :param chain_ids: 선택된 Chain ID (string) 를 담고있는 list
        """
        assert len(self.models) == 1
        if not chain_ids:
            return

        _atoms = [atom for atom in self.models[0].atoms if atom.chain in chain_ids]
        self.models[0].atoms = _atoms

        _seqres = dict()
        for chain_id, residues in self.seqres.items():
            if chain_id not in chain_ids:
                continue

            if chain_id not in _seqres:
                _seqres[chain_id] = []
            _seqres[chain_id] = residues
        self.seqres = _seqres

    def delete_hydrogen_atoms(self, protonation_states_only=False):
        """
        수소원자 전체 삭제

        :param protonation_states_only: protonation state와 관련하여 추후 preparation 및 simulation 단계에서 에러를 유발할 수 있는 수소원자만 삭제할 것인지 여부 (아직 미구현)
        """
        assert len(self.models) == 1
        _atoms = []
        for atom in self.models[0].atoms:
            if atom.elem in ('H', 'D'):
                if not protonation_states_only:
                    continue
                else:  # TODO
                    # residue가 HIS인 경우
                    # residue가 ASP인 경우
                    # residue가 LYS인 경우
                    # 기타등등 ...
                    continue
            _atoms.append(atom)
        self.models[0].atoms = _atoms

    def process_altloc(self):
        """
        PDB의 ATOM 중에 altloc이 있는 경우 A를 제외한 나머지 것을 삭제함
        """
        assert len(self.models) == 1
        _atoms = [atom for atom in self.models[0].atoms if not atom.altloc or atom.altloc == 'A']
        self.models[0].atoms = _atoms

    def process_icode(self):
        """
        PDB의 ATOM 중에 insertion code가 있는 경우 첫 번째 것을 제외한 나머지 것을 삭제함
        """
        assert len(self.models) == 1
        _icode_residues = dict()
        for atom in self.models[0].atoms:
            if atom.resnum not in _icode_residues:
                _icode_residues[atom.resnum] = []
            _icode_residues[atom.resnum].append(atom.icode)

        _atoms = []
        for atom in self.models[0].atoms:
            assert len(_icode_residues[atom.resnum]) > 0
            if len(_icode_residues[atom.resnum]) == 1 or atom.icode == _icode_residues[atom.resnum][0]:
                _atoms.append(atom)

        self.models[0].atoms = _atoms

    def process_solvent_ions(self, solvent_ions):
        assert len(self.models) == 1
        _atoms = []
        for atom in self.models[0].atoms:
            if atom.resname in RESSOLV and [atom.chain, atom.resname] not in solvent_ions:
                continue
            _atoms.append(atom)
        self.models[0].atoms = _atoms

    def process_hetero(self, ligand_name=None):
        """
        DNA, Solvent, ligand 등 hetero atom 삭제
        특정 ligand의 ligand_name을 지정하는 경우 해당 residue는 삭제하지 않음

        :param ligand_name: 삭제하지 않고 남겨둘 ligand의 ligand_name (한 종류만 가능)
        """
        assert len(self.models) == 1
        _atoms = []
        for atom in self.models[0].atoms:
            if atom.resname in RESNA:
                continue
            if atom.record == 'HETATM':
                if ligand_name and ligand_name == atom.resname:
                    pass
                elif atom.resname in RESSOLV:
                    pass
                elif atom.resname in NON_STANDARD:
                    pass
                else:
                    continue
            _atoms.append(atom)
        self.models[0].atoms = _atoms

    def process_non_standards(self):
        """
        비표준 아미노산에 대하여 추후 preparation 단계에서 표준 아미노산으로 인식하도록 residue name을 변경
        """
        assert len(self.models) == 1
        _atoms = []
        for atom in self.models[0].atoms:
            if atom.resname in NON_STANDARD:
                atom.resname = NON_STANDARD[atom.resname]
                if atom.name not in AA_ATOMS[atom.resname]:
                    continue
            _atoms.append(atom)
        self.models[0].atoms = _atoms

    def process_disulfide_bonds(self, cyx_residues=None):
        assert len(self.models) == 1
        _cyx_residues = set()
        for iatm, jatm, _ in self.disulfide_bond_candidates:
            _cyx_residues.add((iatm[1], iatm[2]))
            _cyx_residues.add((jatm[1], jatm[2]))

        _cyx_residues = cyx_residues if cyx_residues else [list(res) for res in _cyx_residues]
        for atom in self.models[0].atoms:
            if [atom.chain, atom.resnum] in _cyx_residues:
                atom.resname = 'CYX'

    def process_protonation_states(self, protonation_states=None):
        assert len(self.models) == 1
        for atom in self.models[0].atoms:
            key = '%s-%s' % (atom.chain, atom.resnum)
            if protonation_states and key in protonation_states:
                atom.resname = protonation_states[key]

    def deserialize(self):
        assert len(self.models) == 1
        lines = []
        for chain, residues in self.seqres.items():
            for i in range(int(len(residues) / 13) + 1):
                if 13*i+12 < len(residues):
                    residues_line = ' '.join(residues[13 * i:13 * i + 12])
                else:
                    residues_line = ' '.join(residues[13 * i:])
                lines.append('SEQRES %3d %s %4d  %s' % (i + 1, chain, len(residues), residues_line))
        lines.extend([atom.deserialize() for atom in self.models[0].atoms])
        return '\n'.join(lines)

    def analyze(self):
        return {
            "models": [i for i in range(len(self.models))],
            "chains": self.chains,
            "sequence": self.sequence,
            "non_standards": self.non_standards,
            "disulfide_bond_candidates": self.disulfide_bond_candidates,
            "protonation_states": self.protonation_states,
            "solvent_ions": self.solvent_ions,
            # "seqres": self.seqres,
        }

    def cleanup(self, model_index=0, chain_ids=tuple(), solvent_ions=tuple(), ligand_name=None):
        self.select_model(model_index)
        self.select_chains(chain_ids)
        self.delete_hydrogen_atoms()
        self.process_altloc()
        self.process_icode()
        self.process_solvent_ions(solvent_ions=solvent_ions)
        self.process_hetero(ligand_name)
        return self

    def create_model(self, cyx_residues=None, protonation_states=None):
        assert len(self.models) == 1
        self.process_non_standards()
        self.process_disulfide_bonds(cyx_residues)
        self.process_protonation_states(protonation_states)
        return self


def run(pdb_file, model_index=0, chain_ids=None, ligand_name=None):
    """
    :param pdb_file:
    :param model_index:
    :param chain_ids:
    :param ligand_name:
    :return:
    """
    with open(pdb_file, 'r') as f:
        topo = Topology(f)
        _content = topo.cleanup(model_index, chain_ids, ligand_name)
        return _content


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('pdb_file')
    parser.add_argument('-m', '--model', type=int, default=0)
    parser.add_argument('-c', '--chains', nargs='+')
    parser.add_argument('-l', '--ligand-name')
    args = parser.parse_args()
    pdb_content = run(args.pdb_file, model_index=args.model, chain_ids=args.chains, ligand_name=args.ligand_name)
    print(pdb_content, end='')

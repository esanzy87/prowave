"""
Core Models
"""
import os
import shutil
import subprocess
from functools import wraps

import yaml
from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from prowave.utils import get_rcsb_pdb, save_uploaded_pdb
from prowave.utils.pdbutil import Topology


def working_directory(directory):
    """
    Decorated 함수를 지정된 working directory에서 수행하도록 하는 데코레이터
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cwd = os.getcwd()
            try:
                os.chdir(directory)
                return func(*args, **kwargs)
            finally:
                os.chdir(cwd)
        return wrapper
    return decorator


# Create your models here.
class UserMeta(models.Model):
    """
    deprecated
    """
    user = models.OneToOneField(User, related_name='meta',
                                on_delete=models.CASCADE)
    organization = models.CharField(max_length=500)


class WorkJob(models.Model):
    """
    WebmdWorkJob
    """
    job_id = models.IntegerField(primary_key=True)
    work_id = models.IntegerField()


class WorkHistory(models.Model):
    """
    WebmdWorkHistory
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    work_id = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    first_name = models.CharField(max_length=500)
    last_name = models.CharField(max_length=500)
    email = models.CharField(max_length=200)
    organization = models.CharField(max_length=500)
    file = models.CharField(max_length=500)
    cut = models.FloatField(default=9.0)
    buffer_size = models.FloatField(default=10.0)
    solvent_model = models.CharField(max_length=15, default='TIP3PBOX')
    cation = models.CharField(max_length=5, default='Na+')
    anion = models.CharField(max_length=5, default='Cl-')
    ref_temp = models.IntegerField(default=300)


class Project(models.Model):
    """
    Project
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='projects',
                              on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)

    @property
    def trajectories(self):
        """
        Project.trajectories
        """
        return Work.objects.filter(project=self).all()

class Work(models.Model):
    """
    Trajectory
    """
    STATUS_CHOICES = (
        'NO DATA',
        'DONE',
        'WAIT',
        'ERROR',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, related_name='works',
                              on_delete=models.CASCADE)
    name = models.CharField(max_length=20, default="Default Work")
    nres = models.IntegerField(default=0)  # Protein residue 길이
    filename = models.CharField(max_length=500, default='', blank=True)
    uploaded = models.BooleanField(default=False)
    cut = models.FloatField(default=9.0)  # cut
    buffer_size = models.FloatField(default=10.0)  # water buffer size
    solvent_model = models.CharField(max_length=15)  # Solvent Model
    work_dir_old = models.CharField(max_length=200, blank=True)  # MD 작업디렉토리
    cation = models.CharField(max_length=5, default='Na+')
    anion = models.CharField(max_length=5, default='Cl-')
    ref_temp = models.IntegerField(default=300)
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    @classmethod
    @transaction.atomic()
    def create(cls, owner, source, project, **kwargs):
        """
        Trajectory.create
        """
        uploaded = source == 'upload'
        instance = cls.objects.create(
            owner=owner,
            project=project,
            uploaded=uploaded,
            solvent_model=kwargs.get('solvent_model', 'TIP3PBOX'),
            buffer_size=kwargs.get('buffer_size', 10.0),
            cut=kwargs.get('cut', 9.0)
        )

        os.makedirs(instance.work_dir, exist_ok=True)
        if source == 'rcsb':
            pdb_id = kwargs.get('pdb_id')
            get_rcsb_pdb(pdb_id, instance.work_dir)
            instance.filename = '%s.pdb' % pdb_id
        else:
            file_obj = kwargs.get('file')
            save_uploaded_pdb(file_obj, instance.work_dir)
            instance.filename = file_obj.name

        if 'name' in kwargs:
            instance.name = kwargs.get('name')

        instance.save()
        return instance

    def cleanup(self, model_index, chain_ids, solvent_ions, ligand_name=None):
        """
        Trajectory.cleanup
        """
        with open(os.path.join(self.work_dir, self.filename), 'r') as stream:
            topo = Topology(stream)
        topo.cleanup(model_index, chain_ids, solvent_ions, ligand_name)
        with open(os.path.join(self.work_dir, 'cleaned.pdb'), 'w') as stream:
            stream.write(topo.deserialize())

    def create_model(self, cyx_residues=None, protonation_states=None):
        """
        Trajectory.create_model
        """
        with open(os.path.join(self.work_dir, 'cleaned.pdb'), 'r') as stream:
            topo = Topology(stream)
        topo.create_model(cyx_residues, protonation_states)
        with open(os.path.join(self.work_dir, 'model.pdb'), 'w') as stream:
            stream.write(topo.deserialize())

    def prepare(self):
        """
        Trajectory.prepare
        """
        subcmd = [
            os.path.join(settings.BASE_DIR, 'webmd/scripts/run_preparation.py'),
            '%d' % self.id,
        ]
        result = self.submit_batch('prep', 'webmd_cpu', subcmd)
        if result['run']:
            template_file = os.path.join(
                settings.BASE_DIR,
                '_artifacts_/simulations_templates/default.yml'
            )
            shutil.copy2(
                template_file,
                os.path.join(self.work_dir, 'simulations.yml')
            )
        return result

    def run_simulation(self, method, index):
        """
        Trajectory.run_simulation
        """
        subcmd = [
            os.path.join(settings.BASE_DIR, 'webmd/scripts/run_simulation.py'),
            '%d' % self.id,
            method,
            '%s' % index
        ]
        return self.submit_batch(method, 'webmd', subcmd)

    def run_analysis(self, method, index):
        """
        Trajectory.run_analysis
        """
        subcmd = [
            os.path.join(settings.BASE_DIR, 'webmd/scripts/run_analysis.py'),
            '%d' % self.id,
            method,
            '%s' % index,
        ]
        return self.submit_batch(method, 'webmd_cpu', subcmd)

    @working_directory('/home/nbcc')
    def submit_batch(self, job_name, partition, subcmd):
        """
        Trajectory.submit_batch
        """
        cmd = [
            os.path.join(settings.SLURM_HOME, 'bin/sbatch'),
            '--job-name', job_name,
            '--partition', partition,
        ]

        cmd.extend(subcmd)
        output = subprocess.check_output(cmd)
        job_id = output.decode().split()[-1]
        try:
            slurm_job_id = int(job_id)
            slurm_job_id_file = os.path.join(self.work_dir, 'slurm_job_id')
            with open(slurm_job_id_file, 'w') as stream:
                stream.write('%d' % slurm_job_id)
            return {
                'run': True,
                'slurm_job_id': slurm_job_id,
                'trajectory_id': self.id
            }
        except ValueError:
            return {
                'run': False,
                'slurm_job_id': -1,
                'trajectory_id': self.id
            }


    @property
    def slurm_job_id(self):
        """
        SLURM job id
        """
        slurm_job_id_file = os.path.join(self.work_dir, 'slurm_job_id')
        try:
            with open(slurm_job_id_file, 'r') as stream:
                return int(stream.read())
        except (ValueError, FileNotFoundError):
            return -1

    @property
    def running(self):
        """
        이 Trajectory가 batch한 task가 현재 실행중인지 체크
        """
        squeue_lines = subprocess.check_output(['squeue', '-h']).decode().split('\n')
        for line in squeue_lines:
            job_status = line.strip().split()
            if job_status and self.slurm_job_id == int(job_status[0]):
                return True
        return False

    @property
    def pdb(self):
        """
        Modelling 절차상 최종으로 생성된 pdb 파일
        """
        for pdb_file in ['model_solv.pdb', 'model.pdb', 'cleaned.pdb']:
            if os.path.exists(os.path.join(self.work_dir, pdb_file)):
                return pdb_file
        return self.filename

    @property
    def work_dir(self):
        """
        work_dir
        """
        return os.path.join(settings.WEBMD_DATA_DIR, '%d' % self.id)

    @property
    def model_params(self):
        """
        MODEL parameters
        Modeller에서 사용되는 파라메터
        """
        with open(os.path.join(self.work_dir, self.filename), 'r') as stream:
            topo = Topology(stream)

        params = {
            'models': [i for i in range(len(topo.models))],
            'chains': topo.chains,
            'solvent_ions': topo.solvent_ions,
            'non_standards': [],
            'disulfide_bond_candidates': [],
            'protonation_states': [],
        }
        cleaned_pdb_file = os.path.join(self.work_dir, 'cleaned.pdb')
        if os.path.exists(cleaned_pdb_file):
            with open(cleaned_pdb_file, 'r') as stream:
                cleaned_topo = Topology(stream)
            params['non_standards'] = cleaned_topo.non_standards
            params['disulfide_bond_candidates'] = cleaned_topo.disulfide_bond_candidates
            params['protonation_states'] = cleaned_topo.protonation_states
        return params

    @property
    def is_modelled(self):
        return os.path.exists(os.path.join(self.work_dir, 'model_solv.pdb'))

    @property
    def simulations(self):
        """
        simulations
        """
        simulations_file = os.path.join(self.work_dir, 'simulations.yml')
        if not os.path.exists(simulations_file):
            return None

        with open(simulations_file, 'r') as stream:
            sim = yaml.load(stream, Loader=yaml.Loader)

        previous = dict()
        for method, items in sim.items():
            for i, item in enumerate(items):
                pdb_path = os.path.join(self.work_dir, '%s.pdb' % item['basename'])
                item['done'] = os.path.exists(pdb_path)
                item['deletable'] = True
                item['runnable'] = False
                item['running'] = False
                if item['done']:
                    if previous:
                        key, idx, _ = previous.values()
                        sim[key][idx]['deletable'] = False
                elif not previous or previous['done']:
                    item['runnable'] = not self.running
                    item['running'] = self.running

                base_url = '/api/webmd/files/%d' % self.id
                item['pdb'] = '%s/%s.pdb' % (base_url, item['basename'])
                if method == 'md':
                    item['dcd'] = '%s/%s.dcd' \
                        % (base_url, item['basename'])

                previous = {
                    'method': method,
                    'index': i,
                    'done': item['done'],
                }
        return sim


class WorkAnalysisJob(models.Model):
    """
    WorkAnalysisJob
    """
    job_id = models.IntegerField(primary_key=True)
    work = models.ForeignKey(Work, on_delete=models.SET_NULL, null=True)
    anal_serial = models.IntegerField()

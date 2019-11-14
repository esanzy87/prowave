"""
webmd.models
"""
import glob
import os
import yaml
from yaml import Loader

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction

from prowave.utils.pdb_analyzer import Topology
from prowave.utils import download_pdb_form_rcsb


def getMinMaxValidators(min_value, max_value):
    """
    getMinMaxValidators
    """
    return [MinValueValidator(min_value), MaxValueValidator(max_value)]


# Exceptions 나중에 리팩토링 될 수 있음
class UnauthorizedError(Exception):
    """
    UnauthorizedError
    """


class BaseModel(models.Model):
    """
    BaseModel
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        """
        Meta
        """
        abstract = True


class Project(BaseModel):
    """
    Project
    """
    title = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, related_name='webmd_projects', on_delete=models.SET_NULL, null=True)


class ProteinModelManager(models.Manager):
    @transaction.atomic()
    def create(self, *args, **kwargs):
        is_uploaded = kwargs['is_uploaded']
        project = kwargs['project']

        # create project work dir if not exists
        os.makedirs(project.work_dir, exist_ok=True)

        create_args = dict(
            buffer_size=kwargs.get('buffer_size', 10),
            cation=kwargs.get('cation', 'Na+'),
            anion=kwargs.get('anion', 'Cl-'),
            project=project,
        )

        if not is_uploaded:  # from RCSB
            pdb_id = kwargs['pdb_id'].upper()
            filename = '%s.pdb' % pdb_id
            with open(os.path.join(project.work_dir, filename), 'wb+') as f:
                rcsb_pdb_content = download_pdb_form_rcsb(pdb_id)
                f.write(rcsb_pdb_content)
                create_args['filename'] = filename
                create_args['pdb_id'] = pdb_id
        else:
            file = kwargs['file']
            with open(os.path.join(project.work_dir, '%s.pdb' % file.name), 'wb+') as f:
                for chunk in file.chunks():
                    f.write(chunk)
                create_args['filename'] = file.name
        return super(ProteinModelManager, self).create(**create_args)


def save_rcsb_pdb(pdb_id, target_dir):
    assert os.path.exists(target_dir)
    filename = '%s.pdb' % pdb_id.upper()
    full_file_path  = os.path.join(target_dir, filename)
    with open(full_file_path, 'wb+') as stream:
        pdb_content = download_pdb_form_rcsb(pdb_id)
        stream.write(pdb_content)
    return filename


def save_uploaded_pdb(file, target_dir):
    assert os.path.exists(target_dir)
    filename = '%s.pdb' % file.name
    full_file_path  = os.path.join(target_dir, filename)
    with open(full_file_path, 'wb+') as stream:
        for chunk in file.chunks():
            stream.write(chunk)
    return filename


class Trajectory(BaseModel):
    """
    Trajectory

    States:
    1. Raw PDB file - result of create()
    2. Cleaned PDB file - result of cleanup()
    3. Modelled PDB file without simulations.yml - result of prepare()
    4. Modelled PDB file with simulations.yml and no simulated trajectories - result of simulations.setter
    5. Modelled PDB file with simulations.yml and simulated trajectories - result of run_next()
    """
    seq = models.IntegerField()
    project = models.ForeignKey(Project, related_name='trajectories', on_delete=models.CASCADE)
    filename = models.CharField(max_length=500, blank=True)
    buffer_size = models.FloatField(default=10.0,
                                    validators=getMinMaxValidators(5.0, 20.0))  # 5 ~ 20
    cutoff = models.FloatField(default=9.0, validators=getMinMaxValidators(1.0, 20.0))  # 1 ~ 20
    cation = models.CharField(max_length=10, choices=[('Na+', 'Na+'), ('K+', 'K+')], default='Na+')
    anion = models.CharField(max_length=10, choices=[('Cl-', 'Cl-')], default='Cl-')

    @property
    def work_dir(self):
        """
        working directory of trajectory
        """
        return '{user_id}/trajectories/{seq}'.format(user_id=self.project.owner.id, seq=self.seq)

    @property
    def next_seq(self):
        """
        retrive next sequence number for new trajectory
        """
        last_obj = self.object.filter(project=self.project).order_by('-seq').first()
        return last_obj.seq + 1 if last_obj else 1

    @property
    def original_pdb(self):
        """
        <filename>.pdb
        """
        file_path = os.path.join(self.work_dir, self.filename)
        with open(file_path, 'r') as stream:
            topo = Topology(stream)
        return topo
    
    @property
    def cleaned_pdb(self):
        """
        cleaned.pdb
        """
        file_path = os.path.join(self.work_dir, 'cleaned.pdb')
        with open(file_path, 'r') as stream:
            topo = Topology(stream)
        return topo

    @property
    def model_pdb(self):
        """
        model.pdb
        """
        file_path = os.path.join(self.work_dir, 'model.pdb')
        with open(file_path, 'r') as stream:
            topo = Topology(stream)
        return topo

    @property
    def sequence(self):
        """
        sequence
        """
        return self.original_pdb.sequence

    @property
    def files(self):
        """
        files
        """
        return sorted([os.path.basename(x) for x in glob.glob('{}/*.pdb'.format(self.work_dir))])

    @property
    def base_url(self):
        """
        base url
        """
        scheme = 'http'
        api_host = 'localhost:8000'
        _url = "{scheme}://{api_host}/api/webmd/users/{user_id}/files/projects/{project_seq}/".format(
            scheme=scheme,
            api_host=api_host,
            user_id=self.project.owner.id,
            project_seq=self.project.seq
        )
        return _url

    @property
    def simulations(self):
        """
        simulations getter
        """
        return yaml.load(os.path.join(self.work_dir, 'simulations.yml'), Loader=Loader)

    @simulations.setter
    def simulations(self, new_simulations):
        """
        simulations setter
        """
        self.validate_simulations(new_simulations)
        with os.path.join(self.work_dir, 'simulations.yml') as f:  # pylint: disable=invalid-name
            yaml.dump(new_simulations, f)

    @staticmethod
    def validate_simulations(simulations):
        """
        validate simulations
        """
        try:
            assert isinstance(simulations, dict)
            assert simulations.keys() == ('min', 'eq', 'md', 'name', 'description')
            # TODO: more validation argument new_simulations
        except AssertionError:
            raise ValueError("Not valid simulations protocol")

    @transaction.atomic()
    def create(self, *args, **kwargs):
        """
        create
        """

    def cleanup(self, *args, **kwargs):
        """
        cleanup
        """
        with open(os.path.join(self.work_dir, 'cleaned.pdb'), 'w') as stream:
            stream.write(self.original_pdb.cleanup(**kwargs))

    def prepare(self, *args, **kwargs):
        """
        prepare
        """
        with open(os.path.join(self.work_dir, 'model.pdb'), 'w') as stream:
            stream.write(self.cleaned_pdb.create_model(**kwargs))
        # TODO: Modelling을 수행하는 script를 클러스터에 batch하기

    def run_next(self, *args, **kwargs):
        """
        run_next
        """
        # TODO: 1. Next가 뭔지 파악하기
        # TODO: 2. Next를 실행하는 script를 클러스터에 batch하기


class JobHistory(BaseModel):
    """
    JobHistory
    """
    job_id = models.IntegerField(null=True, default=None)
    description = models.TextField(blank=True, default='')
    node = models.CharField(max_length=10, blank=True, default='')
    project = models.ForeignKey(Project, related_name='jobs', on_delete=models.SET_NULL, null=True, default=None)
    trajectory = models.ForeignKey(Trajectory, related_name='jobs', on_delete=models.SET_NULL, null=True, default=None)
    is_done = models.BooleanField(default=False)

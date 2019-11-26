"""
Core Models
"""
import os
import yaml
from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from prowave.utils import get_rcsb_pdb, save_uploaded_pdb
from prowave.utils.pdbutil import Topology


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
    Work
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
    project = models.ForeignKey(Project, null=True,
                                on_delete=models.SET_NULL)
    is_deleted = models.BooleanField(default=False)

    @classmethod
    @transaction.atomic()
    def create(cls, owner, source, project, solvent_model, buffer_size, cut,
               **kwargs):
        """
        Work.create
        """
        uploaded = source == 'upload'
        instance = cls.objects.create(
            owner=owner,
            project=project,
            uploaded=uploaded,
            solvent_model=solvent_model,
            buffer_size=buffer_size,
            cut=cut
        )
        os.makedirs(instance.work_dir, exist_ok=True)
        if source == 'rcsb':
            pdb_id = kwargs.get('pdb_id')
            filename = '%s.pdb' % pdb_id
            get_rcsb_pdb(pdb_id, instance.work_dir)
        else:
            file = kwargs.get('file')
            filename = file.name
            save_uploaded_pdb(file, instance.work_dir)
        instance.filename = filename
        if 'name' in kwargs:
            instance.name = kwargs.get('name')
        instance.save()
        return instance

    def cleanup(self, model_index=0, chain_ids=tuple(), solvent_ions=tuple(),
                ligand_name=None):
        """
        Work.cleanup
        """
        with open(os.path.join(self.work_dir, self.filename), 'r') as stream:
            topo = Topology(stream)
        topo.cleanup(model_index, chain_ids, solvent_ions, ligand_name)
        with open(os.path.join(self.work_dir, 'cleaned.pdb'), 'w') as stream:
            stream.write(topo.deserialize())

    def create_model(self, cyx_residues=None, protonation_states=None):
        """
        Work.create_model
        """
        with open(os.path.join(self.work_dir, 'cleaned.pdb'), 'r') as stream:
            topo = Topology(stream)
        topo.create_model(cyx_residues, protonation_states)
        with open(os.path.join(self.work_dir, 'model.pdb'), 'w') as stream:
            stream.write(topo.deserialize())

    def prepare(self):
        """
        Work.prepare
        """
        pass

    @property
    def work_dir(self):
        """
        work_dir
        """
        basepath = '%d/trajectories/%d' % (self.owner.id, self.id)
        return os.path.join(settings.WEBMD_USERDATA_DIR, basepath)

    
    def get_topology(self, filename):
        with open(os.path.join(self.work_dir, filename), 'r') as stream:
            topo = Topology(stream)
        return topo

    @property
    def models(self):
        topo = self.get_topology(self.filename)
        return [i for i in range(len(topo.models))]

    @property
    def chains(self):
        topo = self.get_topology(self.filename)
        return topo.chains

    @property
    def solvent_ions(self):
        topo = self.get_topology(self.filename)
        return topo.solvent_ions

    @property
    def non_standards(self):
        if not os.path.exists(os.path.join(self.work_dir, 'cleaned.pdb')):
            return []
        topo = self.get_topology('cleaned.pdb')
        return topo.non_standards
    
    @property
    def disulfide_bond_candidates(self):
        if not os.path.exists(os.path.join(self.work_dir, 'cleaned.pdb')):
            return []
        topo = self.get_topology('cleaned.pdb')
        return topo.disulfide_bond_candidates

    

    @property
    def protonation_states(self):
        if not os.path.exists(os.path.join(self.work_dir, 'cleaned.pdb')):
            return []
        topo = self.get_topology('cleaned.pdb')
        return topo.protonation_states

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

        base_url = '/api/webmd/users/%d/files/trajectories/%d' \
            % (self.owner.id, self.id)

        previous = dict()
        for stage, items in sim.items():
            for j, item in enumerate(items):
                if stage in ('min', 'eq'):
                    base_path = '%s%d.pdb' % (stage, j+1)
                else:
                    base_path = '%d/%s.pdb' % (j+1, stage)
                pdb_path = os.path.join(self.work_dir, stage, base_path)

                item['done'] = os.path.exists(pdb_path)
                if not item['done']:
                    if not previous:
                        item['runnable'] = True
                    else:
                        item['runnable'] = previous['done']
                        previous['deletable'] = item['runnable']
                    item['deletable'] = True
                else:
                    item['pdb'] = '%s/%s/%s' % (base_url, stage, base_path)
                    if stage == 'md':
                        item['dcd'] = '%s/%s/%d/%s.dcd' \
                            % (base_url, stage, j+1, stage)
                    item['deletable'] = False
                previous = item
        return sim


class WorkAnalysisJob(models.Model):
    """
    WorkAnalysisJob
    """
    job_id = models.IntegerField(primary_key=True)
    work = models.ForeignKey(Work, on_delete=models.SET_NULL, null=True)
    anal_serial = models.IntegerField()

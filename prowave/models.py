"""
Prowave models
"""
import os
import json
import subprocess
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from geoip2 import database as geoip2_db
from geoip2.errors import AddressNotFoundError
from prowave.utils import get_rcsb_pdb, save_uploaded_pdb
from prowave.utils.pdbutil import Topology


class UserInfo(models.Model):
    """
    UserInfo
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='info')
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True)

    @property
    def name(self):
        """
        UserInfo.name
        """
        return '%s %s' % (self.user.first_name, self.user.last_name)

    @property
    def email(self):
        """
        UserInfo.email
        """
        return self.user.email

    @property
    def is_active(self):
        """
        UserInfo.is_active
        """
        return self.user.is_active

    @property
    def work_list(self):
        """
        UserInfo.work_list
        """
        return [work for work in self.user.prowave_works.order_by('-created_at').all()[:30]]


class GeoIPMixin:
    """
    GeoIPMixin
    """
    def fill_info(self):
        """
        GeoIPMixin.fill_info
        """
        if self.ip_addr.startswith('172.16') or self.ip_addr == '127.0.0.1':
            self.country_code = 'KR'
            self.country_name = 'Republic of Korea'
            self.latitude = '37.544641'
            self.longitude = '126.966356'
            self.city = 'Seoul'
            self.organization = 'SookMyung Womens university (NBCC)'
            return self

        try:
            citydbfile_path = os.path.join(settings.BASE_DIR, '_artifacts_/GeoLite2-City.mmdb')
            with geoip2_db.Reader(citydbfile_path) as citydb:
                info = citydb.city(self.ip_addr)
                self.country_code = info.country.iso_code if info.country.iso_code else ''
                self.country_name = info.country.name if info.country.name else ''
                self.latitude = info.location.latitude if info.location.latitude else ''
                self.longitude = info.location.longitude if info.location.longitude else ''
                self.city = info.city.name if info.city.name else ''
            asndbfile_path = os.path.join(settings.BASE_DIR, '_artifacts_/GeoLite2-ASN.mmdb')
            with geoip2_db.Reader(asndbfile_path) as asndb:
                info = asndb.asn(self.ip_addr)
                self.organization = info.autonomous_system_organization
        except AddressNotFoundError:
            pass
        return self


# Create your models here.
class History(models.Model, GeoIPMixin):
    """
    History
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visited_url = models.URLField()
    ip_addr = models.GenericIPAddressField()
    country_code = models.CharField(max_length=10)
    country_name = models.CharField(max_length=200)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    city = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=500, blank=True)
    connecton_type = models.CharField(max_length=200, blank=True)
    loggedin_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    @classmethod
    def get_history(cls, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        instance = cls()
        instance.ip_addr = ip
        instance.visited_url = request.POST.get('visited_url')
        try:
            instance.fill_info()
        except:
            instance.country_code = ''
            instance.country_name = ''
            instance.latitude = 0.0
            instance.longitude = 0.0
            instance.city = ''
        return instance

    @classmethod
    def locations(cls):
        histories = cls.objects.distinct('latitude', 'longitude').all()
        return [[x.latitude, x.longitude] for x in histories if x.latitude and x.longitude]


class Work(models.Model):
    """
    Work (Solvation free energy)
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(blank=True)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL,
                              related_name='prowave_works')

    @classmethod
    @transaction.atomic()
    def create(cls, owner, email, mode, source, remote_ip, *args, **kwargs):
        """
        Work.create
        """
        instance = cls.objects.create(email=email, owner=owner)
        if source == 'rcsb':
            pdb_id = kwargs.get('pdb_id')
            filename = '%s.pdb' % pdb_id
            get_rcsb_pdb(pdb_id, instance.work_dir)
        else:
            file = kwargs.get('file')
            filename = file.name
            save_uploaded_pdb(file, instance.work_dir)

        history = WorkHistory.objects.create(
            work_id=instance.id,
            email=email,
            name=owner.info.name if owner else kwargs.get('name'),
            position=owner.info.title if owner else kwargs.get('title'),
            org1=owner.info.organization if owner else kwargs.get('organization'),
            filename=filename,
            ip_addr=remote_ip,
            solvent='TIP3PBOX',
            box_size='128x128x128',
            grid_size='128x128x128',
            mode=mode,
        )
        history.fill_info()
        history.save()
        # cleanup
        with open(os.path.join(instance.work_dir, filename), 'r') as stream:
            topo = Topology(stream)
        cleaned_pdb_content = topo.cleanup().deserialize()
        model_pdb_content = topo.create_model().deserialize()
        with open(os.path.join(instance.work_dir, 'cleaned.pdb'), 'w') as stream:
            stream.write(cleaned_pdb_content)
        with open(os.path.join(instance.work_dir, 'model.pdb'), 'w') as stream:
            stream.write(model_pdb_content)
        return instance

    def run(self):
        """
        Work.run
        """
        sbatch_exe = os.path.join(settings.SLURM_HOME, 'bin/sbatch')
        cwd = os.getcwd()
        try:
            os.chdir('/home/nbcc')
            cmd = [
                sbatch_exe,
                '--job-name', 'SFE',
                '--partition', 'prowave',
                '--gres', 'gpu:1',
                os.path.join(settings.BASE_DIR, 'sfe/scripts/run.py'),
                '%d' % self.id,
                self.history.mode,
            ]
            output = subprocess.check_output(cmd)
            job_id = output.decode().split()[-1]
            try:
                slurm_job_id = int(job_id)
                with open(os.path.join(self.work_dir, 'slurm_job_id'), 'w') as stream:
                    stream.write('%d' % slurm_job_id)
                return {'run': True, 'slurm_job_id': slurm_job_id, 'work_id': self.id}
            except ValueError:
                return {'run': False, 'slurm_job_id': -1, 'work_id': self.id}
        finally:
            os.chdir(cwd)

    @property
    def work_dir(self):
        """
        :return: working directory of SFEWork
        """
        return os.path.abspath(os.path.join(settings.PROWAVE_DATA_DIR, '%d' % self.id))

    @property
    def slurm_job_id(self):
        """
        :return: slum_job_id or -1
        """
        full_file_path = os.path.join(self.work_dir, 'slurm_job_id')
        try:
            assert os.path.exists(full_file_path)
            with open(full_file_path, 'r') as stream:
                return int(stream.read().strip())
        except (AssertionError, ValueError):
            return -1

    @property
    def status(self):
        """
        job execution status
        """
        if os.path.exists(os.path.join(self.work_dir, 'result.json')):
            return {'done': True}

        if self.slurm_job_id > 0:
            squeue_lines = subprocess.check_output(['squeue', '-h']).decode().split('\n')
            for line in squeue_lines:
                job_status = line.strip().split()
                if job_status and self.slurm_job_id == int(job_status[0]):
                    message = "Job is Running on node {} ({})".format(job_status[7], job_status[5])
                    return {'done': False, 'found': True, 'message': message}
        return {'done': False, 'found': False}

    @property
    def result(self):
        """
        :return: content of result.json in dictionary data structure or None
        """
        full_file_path = os.path.join(self.work_dir, 'result.json')
        if os.path.exists(full_file_path):
            with open(full_file_path, 'r') as stream:
                return json.load(stream)
        return None

    @property
    def plot(self):
        """
        :return: content of plot.svg or None
        """
        full_file_path = os.path.join(self.work_dir, 'plot.svg')
        if os.path.exists(full_file_path):
            with open(full_file_path, 'r') as stream:
                return stream.read()
        return None

    @property
    def history(self):
        """
        work_history
        """
        return WorkHistory.objects.filter(work_id=self.id).first()

    @property
    def pdb(self):
        return "/api/solvation-free-energy/works/{}/files/model/".format(self.id)

class WorkJob(models.Model):
    """
    Work Job
    """
    job_id = models.IntegerField()
    work_id = models.IntegerField()
    work_type = models.CharField(
        max_length=50,
        choices=(('sfe', 'Solvation Free Energy'), ('ba', 'Binding Affinity')),
        default='sfe')


class WorkHistory(models.Model, GeoIPMixin):
    """
    Work History
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    work_id = models.IntegerField(null=True)
    email = models.EmailField(blank=True)
    name = models.CharField(max_length=200, blank=True, default='')
    org1 = models.CharField(max_length=500, blank=True, default='')
    ip_addr = models.GenericIPAddressField()
    country_code = models.CharField(max_length=10)
    country_name = models.CharField(max_length=200)
    organization = models.CharField(max_length=500, blank=True)
    filename = models.CharField(max_length=200, blank=True)
    mode = models.CharField(max_length=5)
    solvent = models.CharField(max_length=100)
    box_size = models.CharField(max_length=50)
    grid_size = models.CharField(max_length=50)
    position = models.CharField(max_length=200, blank=True, default='')

    @property
    def owner(self):
        """
        Work history owner
        """
        work = Work.objects.filter(id=self.work_id).first()
        if work:
            return work.owner
        else:
            return None

    @property
    def title(self):
        """
        title of calculation
        """
        title_map = {
            'm': 'Solvation Free Energy (SFE)',
            't': 'Decomposition of SFE into solvation energy and solvation entropy',
            'a': 'Residual decomposition of SFE (Site-Directed Thermodynamics)',
            'x': 'Residual decomposition of SFE into solvation energy and solvation entropy',
        }
        return title_map[self.mode]

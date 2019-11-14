import json
import os
# django modules
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
# 3rd party modules
from geoip2 import database as geoip2_db
from geoip2.errors import AddressNotFoundError
# in project modules
from .mixins import ModellerMixin


def query_geoip(ip_addr):
    if ip_addr.startswith('172.16') or ip_addr == '127.0.0.1':
        return {
            'country_code': 'KR',
            'country_name': 'Republic of Korea',
            'latitude': 37.544641,
            'longitude': 126.966356,
            'city': 'Seoul',
            'organization': 'SookMyung Womens university (NBCC)',
        }
    else:
        city_db_path = os.path.join(settings.BASE_DIR, '_artifacts_/GeoLite2-City.mmdb')
        asn_db_path = os.path.join(settings.BASE_DIR, '_artifacts_/GeoLite2-ASN.mmdb')
        with geoip2_db.Reader(city_db_path) as g:
            city_info = g.city(ip_addr)
        with geoip2_db.Reader(asn_db_path) as asn:
            asn_info = asn.asn(ip_addr)
        return {
            'country_code': city_info.country.iso_code,
            'country_name': city_info.country.name,
            'latitude': city_info.location.latitude,
            'longitude': city_info.location.longitude,
            'city': city_info.city.name,
            'organization': asn_info.autonomous_system_organization,
        }


class History(models.Model):
    """
    사이트 접속 히스토리
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
    organization = models.CharField(max_length=200, blank=True)
    loggedin_user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class Work(models.Model, ModellerMixin):
    """
    Solvation Free Energy 계산작업
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(blank=True)
    owner = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="prowave_works")

    @property
    def work_dir(self):
        return os.path.join(settings.PROWAVE_DATA_DIR, '%d' % self.id)

    @property
    def result(self):
        file_path = os.path.join(self.work_dir, 'result.json')
        if os.path.exists(file_path):
            with open(os.path.join(self.work_dir, 'result.json'), 'r') as f:
                return json.load(f)
        return {}

    @property
    def slurm_job_id(self):
        file_path = os.path.join(self.work_dir, 'slurm_job_id')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return int(f.read().strip())
        return -1

    @property
    def plot(self):
        file_path = os.path.join(self.work_dir, 'plot.svg')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return None


class WorkHistory(models.Model):
    """
    Solvation Free Energy 계산작업 히스토리
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    work = models.OneToOneField(Work, null=True, on_delete=models.SET_NULL, related_name='history')
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

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            info = query_geoip(self.ip_addr)
            self.country_code = info['country_code']
            self.country_name = info['country_name']
            self.organization = info['organization']
        except AddressNotFoundError:
            self.country_code = ''
            self.country_name = ''
            self.organization = ''
        super(WorkHistory, self).save(force_insert, force_update, using, update_fields)

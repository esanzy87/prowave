# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-24 08:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webmd', '0010_auto_20170824_0718'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='work',
            name='md_prep_status',
        ),
        migrations.RemoveField(
            model_name='work',
            name='md_run_status',
        ),
        migrations.RemoveField(
            model_name='work',
            name='ptraj_prep_status',
        ),
        migrations.RemoveField(
            model_name='work',
            name='ptraj_run_status',
        ),
    ]

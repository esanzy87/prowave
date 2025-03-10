# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-21 15:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webmd', '0008_auto_20170820_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='eqjob',
            name='dt',
            field=models.FloatField(default=0.002),
        ),
        migrations.AlterField(
            model_name='eqjob',
            name='init_temp',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='eqjob',
            name='nstlim1',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='eqjob',
            name='nstlim2',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='minjob',
            name='maxcyc1',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='minjob',
            name='maxcyc2',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='minjob',
            name='ncyc1',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='minjob',
            name='ncyc2',
            field=models.IntegerField(default=0),
        ),
    ]

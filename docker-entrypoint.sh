#!/bin/bash
set -e

echo "---> Starting the MUNGE Authentication service (munged) ..."
gosu munge /usr/sbin/munged

echo "---> Starting the slurmctld service ..."
gosu root /opt/apps/slurm/sbin/slurmctld

echo "---> Starting ProWaVE web service ..."
cd /home/nbcc/www/prowave && gosu nbcc python manage.py runserver 0.0.0.0:8000

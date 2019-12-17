#!/bin/bash
set -e

echo "---> Starting the MUNGE Authentication service (munged) ..."
gosu munge /usr/sbin/munged

echo "---> Starting the slurmd service ..."
gosu root /opt/apps/slurm/sbin/slurmd

# prevent container from exiting
tailf /dev/null

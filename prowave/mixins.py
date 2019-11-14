import glob
import os
import requests
import subprocess
from django.conf import settings


class ModellerMixin:
    work_dir: str


class SlurmMixin:
    work_dir: str

    def submit_batch(self, base_name, sub_cmd, partition=None, dependency=None, gres=None):
        """
        Slurm workload manager에 작업을 위임하기 위한 함수

        :param base_name:
        :param sub_cmd:
        :param partition:
        :param dependency:
        :param gres:
        :return:
        """
        sbatch_exe = os.path.join(settings.SLURM_HOME, 'bin/sbatch')
        assert os.path.exists(sbatch_exe)
        assert os.path.exists(self.work_dir)
        cwd = os.getcwd()
        try:
            os.chdir('/home/nbcc')
            cmd = [sbatch_exe, '--job-name', base_name]
            if partition:
                cmd += ['--partition', partition]
            if dependency:
                cmd += ['--dependency', dependency]
            if gres:
                cmd += ['--gres', gres]
            cmd += sub_cmd
            output = subprocess.check_output(cmd)
            job_id = output.decode().split()[-1]
            try:
                return int(job_id)
            except ValueError:
                return -1
        finally:
            os.chdir(cwd)

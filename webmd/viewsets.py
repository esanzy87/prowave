# pylint: disable=invalid-name
"""
webmd.viewsets

<< PROJECT API >>
/api/webmd/projects/ [GET, POST]
[GET] fetch project list
[POST] create a new project

/api/webmd/projects/<project_id>/ [GET]
[GET] fetch project detail

/api/webmd/projects/<project_id>/protein-model/ [GET, POST, DELETE]
[GET] fetch protein model of a project
[POST] create protein model of a project
[DELETE] delete exist protein model of a project

/api/webmd/projects/<project_id>/protein-model/run/ [POST]
[POST] batch protein modelling job to computing cluster


<< TRAJECTORY API >>
/api/webmd/trajectories/ [GET, POST]
[GET] fetch trajectory list
[POST] create a new trajectory

/api/webmd/trajectories/<trajectory_id>/ [GET, DELETE]
[GET] fetch trajectory detail with simulation status
[DELETE] delete (disable) whole trajectory

/api/webmd/trajectories/<trajectory_id>/protein-model/ [POST, PUT, DELETE]
[POST] create a new protein model of trajectory
[DELETE] delete protein model of trajectory
[PUT] run modelling

/api/webmd/trajectories/<trajectory_id>/simulations/ [POST, PUT]
[POST] create or edit simulation protocol
[PUT] run next simulation

<< ANALYSIS API >>
/api/webmd/analyses/ [GET, POST]

/api/webmd/analyses/<analysis_id>/ [GET]

/api/webmd/analyses/<analysis_id/

"""
import os
import subprocess
from django.conf import settings
from django.db import transaction
from rest_framework import viewsets, routers, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Project, Work as Trajectory
from .serializers import ProjectSerializer, TrajectorySerializer


class TrajectoryViewSet(viewsets.ModelViewSet):
    """
    webmd.viewsets.WebmdWorkViewset
    """
    queryset = Trajectory.objects
    serializer_class = TrajectorySerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(owner=self.request.user)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    webmd.viewsets.ProjectViewSet
    """
    queryset = Project.objects
    serializer_class = ProjectSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(owner=self.request.user)

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        webmd.viewsets.ProjectViewSet.create
        """
        if request.user.is_authenticated:
            instance = Project.objects.create(
                subject=request.data.get('subject', 'WebMD Project'),
                owner=request.user
            )
            return Response(data=self.serializer_class(instance).data)
        else:
            raise PermissionDenied

    @action(['GET', 'POST', 'DELETE'], url_path='protein-model', detail=True)
    def protein_model(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        webmd.viewsets.ProjectViewSet.protein_model
        """
        project = self.get_object()
        model_pdb_file = os.path.join(project.work_dir, 'model.pdb')
        cleaned_pdb_file = os.path.join(project.work_dir, 'cleaned.pdb')

        if request.method == 'POST':
            try:
                model_index = int(request.data.get('model', '0'))
            except TypeError:
                model_index = 0
            chain_ids = request.data.get('chains', [])
            solvent_ions = request.data.get('solvent_ions', [])
            ligand_name = request.data.get('ligand_name', None)
            project.protein_model.cleanup(
                model_index=model_index,
                chain_ids=chain_ids,
                solvent_ions=solvent_ions,
                ligand_name=ligand_name
            )
            assert os.path.exists(cleaned_pdb_file)

        if request.method == 'DELETE':
            if os.path.exists(model_pdb_file):
                os.remove(model_pdb_file)
                os.remove(os.path.join(project.work_dir, 'leaprc'))
                os.remove(os.path.join(project.work_dir, 'leap.log'))
                os.remove(os.path.join(project.work_dir, 'model.inpcrd'))
                os.remove(os.path.join(project.work_dir, 'model.prmtop'))
                os.remove(os.path.join(project.work_dir, 'model_solv.pdb'))
                os.remove(os.path.join(project.work_dir, 'slurm_job_id'))
            elif os.path.exists(cleaned_pdb_file):
                os.remove(cleaned_pdb_file)
            else:
                pass

        topo = project.protein_model.topology
        if os.path.exists(model_pdb_file):
            return Response({
                'stage': 3,
                'chains': topo.chains,
                'sequence': topo.sequence,
                'pdb': '{}{}'.format(project.protein_model.base_url, 'model.pdb')
            })
        elif os.path.exists(cleaned_pdb_file):
            return Response({
                'stage': 2,
                'chains': topo.chains,
                'nonStandards': topo.non_standards,
                'disulfideBondCandidates': topo.disulfide_bond_candidates,
                'protonationStates': topo.protonation_states,
                'sequence': topo.sequence,
                'pdb': '{}{}'.format(project.protein_model.base_url, 'cleaned.pdb'),
            })
        else:
            base_url = project.protein_model.base_url
            filename = project.protein_model.filename
            return Response({
                'stage': 1,
                'models': range(len(topo.models)),
                'chains': topo.chains,
                'solventIons': topo.solvent_ions,
                'sequence': topo.sequence,
                'pdb': '{}/{}'.format(base_url, filename),
            })

    @action(['POST'], url_path='protein-model/run', detail=True)
    def run_protein_modelling(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        webmd.viewsets.ProjectViewSet.run_protein_modelling
        """
        project = self.get_object()
        cyx_residues = request.data.get('cyx_residues', [])
        protonation_states = request.data.get('protonation_states', [])
        project.protein_model.create_model(
            cyx_residues=cyx_residues,
            protonation_states=protonation_states
        )
        # submit job to work load manager
        sbatch_exe = os.path.join(settings.SLURM_HOME, 'bin/sbatch')
        cwd = os.getcwd()
        try:
            os.chdir('/home/nbcc')
            cmd = [
                sbatch_exe,
                '--job-name', 'TLEAP',
                '--partition', 'prowave_cpu',
                os.path.join(settings.BASE_DIR, 'webmd/scripts/run_modelling.py'),
                '%s' % project.owner_id,
                '%s' % project.seq,
            ]
            output = subprocess.check_output(cmd)
            job_id = output.decode().split()[-1]
            try:
                slurm_job_id = int(job_id)
                with open(os.path.join(project.work_dir, 'slurm_job_id'), 'w') as f:
                    f.write('%d' % slurm_job_id)
                return Response({
                    'run': True,
                    'slurm_job_id': slurm_job_id,
                    'project_id': project.id
                })
            except ValueError:
                return Response({
                    'run': False,
                    'slurm_job_id': -1,
                    'project_id': project.id
                })
        finally:
            os.chdir(cwd)


router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'trajectories', TrajectoryViewSet)

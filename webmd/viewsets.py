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
from rest_framework import viewsets, routers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser

from prowave.utils import get_rcsb_pdb, save_uploaded_pdb
from .models import Project, Work as Trajectory
from .serializers import ProjectSerializer, TrajectorySerializer


class TrajectoryViewSet(viewsets.ModelViewSet):
    """
    webmd.viewsets.TrajectoryViewSet
    """
    queryset = Trajectory.objects
    serializer_class = TrajectorySerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(owner=self.request.user)

    @action(['POST'], url_path='cleanup', detail=True)
    def cleanup(self, request, *args, **kwargs):
        """
        webmd.viewsets.TrajectoryViewSet.cleanup
        """
        trajectory = self.get_object()
        try:
            model_index = int(request.data.get('model', '0'))
        except TypeError:
            model_index = 0
        chain_ids = request.data.get('chain_ids', [])
        solvent_ions = request.data.get('solvent_ions', [])
        ligand_name = request.data.get('ligand_name')
        trajectory.cleanup(model_index, chain_ids, solvent_ions, ligand_name)
        return self.retrieve(request, *args, **kwargs)

    @action(['POST', 'DELETE'], url_path='protein-model', detail=True)
    def protein_model(self, request, *args, **kwargs):
        """
        webmd.viewsets.TrajectoryViewSet.protein_model
        """
        trajectory = self.get_object()

        if request.method == 'DELETE':
            for target_file in ('model.pdb', 'leaprc', 'leap.log', 'model.inpcrd', 'model.prmtop', 'model_solv.pdb', 'slurm_job_id'):
                if os.path.exists(os.path.join(trajectory.work_dir, target_file)):
                    os.remove(os.path.join(trajectory.work_dir, target_file))
            return self.retrieve(request, *args, **kwargs)

        if request.method == 'POST':
            cyx_residues = request.data.get('cyx_residues', [])
            protonation_states = request.data.get('protonation_states', [])
            trajectory.create_model(cyx_residues, protonation_states)
            return Response(trajectory.prepare())
        return self.retrieve(request, *args, **kwargs)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    webmd.viewsets.ProjectViewSet
    """
    queryset = Project.objects
    serializer_class = ProjectSerializer
    parser_classes = (FormParser, MultiPartParser)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(owner=self.request.user).order_by('-created_at')

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        webmd.viewsets.ProjectViewSet.create
        """
        if not request.user.is_authenticated:
            return PermissionDenied

        instance = Project.objects.create(
            subject=request.data.get('subject', 'WebMD Project'),
            owner=request.user
        )

        create_args = dict(
            owner=request.user,
            source=request.data['source'],
            project=instance,
            pdb_id=request.data['pdb_id'],
            solvent_model=request.data.get('water_model', 'TIP3PBOX'),
            buffer_size=request.data.get('buffer_size', 10.0),
            cut=request.data.get('cut', 9.0),
            cation=request.data.get('cation', 'Na+'),
            anion=request.data.get('anion', 'Cl-'),
            name='Trajectory A'
        )

        if request.data['source'] == 'rcsb':
            create_args['pdb_id'] = request.data['pdb_id']
        else:
            create_args['file'] = request.data['pdb_file']

        Trajectory.create(**create_args)
        return Response(data=self.serializer_class(instance).data)

router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'trajectories', TrajectoryViewSet)

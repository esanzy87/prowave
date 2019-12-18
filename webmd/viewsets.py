# pylint: disable=invalid-name
"""
webmd.viewsets

"""
import csv
import os
from glob import glob
from io import BytesIO

import matplotlib
import numpy as np
import yaml
from django.db import transaction
from django.http.response import HttpResponse
from rest_framework import viewsets, routers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Project, Work as Trajectory
from .serializers import ProjectSerializer, TrajectorySerializer


matplotlib.use('Agg')


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
            model_index = int(request.data.get('model_index', '0'))
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
            files = (
                'model.pdb', 'leaprc', 'leap.log', 'model.inpcrd',
                'model.prmtop', 'model_solv.pdb', 'slurm_job_id'
            )
            for target_file in files:
                file_path = os.path.join(trajectory.work_dir, target_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            return self.retrieve(request, *args, **kwargs)

        if request.method == 'POST':
            cyx_residues = request.data.get('cyx_residues', [])
            protonation_states = request.data.get('protonation_states', [])
            trajectory.create_model(cyx_residues, protonation_states)
            return Response(trajectory.prepare())
        return self.retrieve(request, *args, **kwargs)

    @action(['GET', 'POST', 'PUT', 'DELETE'], url_path='simulations', detail=True)
    def simulations(self, request, pk=None):
        """
        webmd.viewsets.TrajectoryViewSet.simulations
        """
        trajectory = self.get_object()
        simulations_file_path = os.path.join(trajectory.work_dir, 'simulations.yml')

        if request.method == 'POST':
            method = request.data.get('method')
            index = request.data.get('index')
            params = request.data.get('params')
            simulations = yaml.load(simulations_file_path, Loader=yaml.Loader)

            params['reference'] = '{method}/{method}{index}.npz'.format(method=method, index=index)
            params['state_file'] = '{method}/{method}{index}.npz'.format(method=method, index=index+1)
            params['pdb_file'] = '{method}/{method}{index}.pdb'.format(method=method, index=index+1)

            if method in ('eq', 'md'):
                params['out_file'] = '{method}/{method}{index}.out'.format(method=method, index=index+1)

            if method == 'md':
                params['traj_file'] = '{method}/{method}{index}.dcd'.format(method=method, index=index+1)

            simulations[method].append(params)

            with open(simulations_file_path, 'w') as stream:
                stream.write(yaml.dump(simulations, Dumper=yaml.Dumper))
        elif request.method == 'PUT':
            method = request.data.get('method')
            index = request.data.get('index')
            params = request.data.get('params')
            simulations = yaml.load(simulations_file_path, Loader=yaml.Loader)
            for key, value in params.items():
                simulations[method][index][key] = value

            with open(simulations_file_path, 'w') as stream:
                stream.write(yaml.dump(simulations, Dumper=yaml.Dumper))
        elif request.method == 'DELETE':
            pass

        return Response(trajectory.simulations)

    @action(['POST'], url_path='run', detail=True)
    def run_simulation(self, request, pk=None):
        """
        webmd.viewsets.TrajectoryViewSet.run_simulation
        """
        trajectory = self.get_object()
        method = request.data.get('method')
        index = request.data.get('index')
        return Response(trajectory.run_simulation(method, index))


    @action(['GET'], url_path='analyses', detail=True)
    def analyses(self, request, pk=None):
        """
        webmd.viewsets.TrajectoryViewSet.analyses
        """
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()

        trajectory = self.get_object()
        method = request.GET.get('method')
        assert method in ('rmsd', 'rmsf', 'radgyr', 'sasa')

        if method == 'rmsd':
            result = [0.0]
            for csv_file in glob(os.path.join(trajectory.work_dir, 'analyses', '%s*.out' % method)):
                with open(csv_file, 'r') as stream:
                    rows = csv.reader(stream, delimiter='\t')
                    for row in rows:
                        try:
                            result.append(float(row[0]))
                        except ValueError:
                            pass

            ax.plot([(i * 5) for i in range(len(result))], result)
            ax.set_xlabel('Time (ps)')
            ax.set_ylabel('RMSD (Å)')
        if method == 'rmsf':
            results = []
            for csv_file in glob(os.path.join(trajectory.work_dir, 'analyses', '%s*.out' % method)):
                with open(csv_file, 'r') as stream:
                    result = []
                    rows = csv.reader(stream, delimiter='\t')
                    for row in rows:
                        try:
                            result.append(float(row[0]))
                        except ValueError:
                            pass
                results.append(result)
            result = np.average(np.array(results), axis=0)
            ax.plot(range(1, len(result)+1), result)
            ax.set_xlabel('Residue Number')
            ax.set_ylabel('RMSF (Å)')
        if method == 'radgyr':
            result = []
            for csv_file in glob(os.path.join(trajectory.work_dir, 'analyses', '%s*.out' % method)):
                with open(csv_file, 'r') as stream:
                    rows = csv.reader(stream, delimiter='\t')
                    for row in rows:
                        try:
                            result.append(float(row[0]))
                        except ValueError:
                            pass

            window = 5
            cumsum = np.cumsum(result)
            cumsum[window:] = cumsum[window:] - cumsum[:-window]
            rolling_mean = cumsum[window-1:] / window
            ax.plot([(i * 5) for i in range(len(result))], result, color='#dddddd')
            ax.plot([(i * 5) for i in range(window, len(result)+1)], rolling_mean)
            # ax.plot([(i * 5) for i in range(len(result))], result)
            ax.set_xlabel('Time (ps)')
            ax.set_ylabel('Radius of Gyration (radian)')
        if method == 'sasa':
            result = []
            for csv_file in glob(os.path.join(trajectory.work_dir, 'analyses', '%s*.out' % method)):
                with open(csv_file, 'r') as stream:
                    rows = csv.reader(stream, delimiter='\t')
                    for row in rows:
                        try:
                            result.append(float(row[0]))
                        except ValueError:
                            pass

            window = 5
            cumsum = np.cumsum(result)
            cumsum[window:] = cumsum[window:] - cumsum[:-window]
            rolling_mean = cumsum[window-1:] / window
            ax.plot([(i * 5) for i in range(len(result))], result, color='#dddddd')
            ax.plot([(i * 5) for i in range(window, len(result)+1)], rolling_mean)
            ax.set_xlabel('Time (ps)')
            ax.set_ylabel('SASA (nm^2)')

        image_data = BytesIO()
        fig.tight_layout()
        fig.savefig(image_data, format='svg', box_inches='tight')
        image_data.seek(0)        
        return HttpResponse(image_data, 'image/svg')

    @action(['POST'], url_path='analyses/run', detail=True)
    def run_analysis(self, request, pk=None):
        """
        webmd.viewsets.TrajectoryViewSet.run_analysis
        """
        trajectory = self.get_object()
        method = request.data.get('method')
        index = request.data.get('index')
        return Response(trajectory.run_analysis(method, index))


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

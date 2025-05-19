from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.models import User
from .models import Project, DynamicTable, DynamicData
from .serializers import *
from .permissions import *
from django.shortcuts import get_object_or_404
from uuid import uuid4
import copy
from django.utils.dateparse import parse_date
from asteval import Interpreter

class PostTableView(APIView):
    permission_classes = [IsCoachOrAdmin]

    def post(self, request):
        serializer = TableCreateSerializer(data=request.data)
        if serializer.is_valid():
            project = get_object_or_404(Project, name=serializer.validated_data['project'])
            if request.user.userprofile.project != project:
                return Response({'error': 'No permission'}, status=403)
            DynamicTable.objects.create(
                title=serializer.validated_data['Title'],
                project=project,
                schema=serializer.validated_data['data']
            )
            return Response({'message': 'Table created'})
        return Response(serializer.errors, status=400)

class PostDataView(APIView):
    permission_classes = [IsAthleteOrAdmin]

    def post(self, request):
        serializer = DataSubmitSerializer(data=request.data)
        if serializer.is_valid():
            table = get_object_or_404(DynamicTable, title=serializer.validated_data['Title'])
            if request.user.userprofile.project != table.project:
                return Response({'error': 'No permission'}, status=403)
            for row in serializer.validated_data['data']:
                entry = copy.deepcopy(row)
                for k in entry:
                    entry[k]['Id'] = str(uuid4())
                DynamicData.objects.create(table=table, row=entry, submitted_by=request.user)
            return Response({'message': 'Data submitted'})
        return Response(serializer.errors, status=400)

class GetTableDataView(APIView):
    def get(self, request, title):
        table = get_object_or_404(DynamicTable, title=title)
        if request.user.userprofile.project != table.project:
            return Response({'error': 'No permission'}, status=403)

        role = request.user.userprofile.role
        data_qs = DynamicData.objects.filter(table=table)

        # Optional filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        athlete_username = request.query_params.get('athlete')

        if role == 'athlete':
            data_qs = data_qs.filter(submitted_by=request.user)
        elif role in ['coach', 'admin'] and athlete_username:
            athlete_user = get_object_or_404(User, username=athlete_username)
            if not hasattr(athlete_user, 'userprofile') or athlete_user.userprofile.project != table.project:
                return Response({'error': 'Athlete not in project'}, status=403)
            data_qs = data_qs.filter(submitted_by=athlete_user)

        # Apply date filtering if provided
        if start_date:
            try:
                start = parse_date(start_date)
                if start:
                    data_qs = data_qs.filter(created_at__date__gte=start)
            except ValueError:
                return Response({'error': 'Invalid start_date format. Use YYYY-MM-DD'}, status=400)
        if end_date:
            try:
                end = parse_date(end_date)
                if end:
                    data_qs = data_qs.filter(created_at__date__lte=end)
            except ValueError:
                return Response({'error': 'Invalid end_date format. Use YYYY-MM-DD'}, status=400)

        data = [entry.row for entry in data_qs]
        return Response({"Title": table.title, "data": data})

class GetTableStructureView(APIView):
    def get(self, request, title):
        table = get_object_or_404(DynamicTable, title=title)
        if request.user.userprofile.project != table.project:
            return Response({'error': 'No permission'}, status=403)
        return Response({"Title": table.title, "project": table.project.name, "data": table.schema})

class UpdateDataView(APIView):
    permission_classes = [IsCoachOrAdmin]

    def post(self, request):
        serializer = DataUpdateSerializer(data=request.data)
        if serializer.is_valid():
            table = get_object_or_404(DynamicTable, title=serializer.validated_data['Title'])
            if request.user.userprofile.project != table.project:
                return Response({'error': 'No permission'}, status=403)
            for row in DynamicData.objects.filter(table=table):
                for key, val in serializer.validated_data['data'].items():
                    if key in row.row:
                        if isinstance(val, dict) and isinstance(row.row[key], dict):
                            row.row[key].update(val)
                        else:
                            row.row[key] = val
                        row.save()
            return Response({'message': 'Data updated'})
        return Response(serializer.errors, status=400)

class ProcessDataView(APIView):
    permission_classes = [IsCoachOrAdmin]

    def post(self, request):
        serializer = ProcessDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        table = get_object_or_404(DynamicTable, title=serializer.validated_data['Title'])
        if request.user.userprofile.project != table.project:
            return Response({'error': 'No permission'}, status=status.HTTP_403_FORBIDDEN)

        result_schema = copy.deepcopy(table.schema)
        result_data = []
        raw_data = DynamicData.objects.filter(table=table)

        aeval = Interpreter()

        for row_obj in raw_data:
            row_result = copy.deepcopy(row_obj.row)

            for item in serializer.validated_data['data']:
                for key, val in item.items():
                    label = val.get("Label") or key
                    expr = val.get("Expression")
                    expected_type = val.get("Type", "unknown")

                    if expr:
                        try:
                            local_env = {
                                k: float(v['Value']) for k, v in row_result.items()
                                if isinstance(v, dict) and 'Value' in v and
                                isinstance(v['Value'], (int, float, str)) and
                                str(v['Value']).replace('.', '', 1).isdigit()
                            }
                            aeval.symtable.clear()
                            aeval.symtable.update(local_env)

                            value = aeval(expr)

                            if expected_type.lower() == 'int':
                                value = int(value)
                            elif expected_type.lower() == 'float':
                                value = float(value)
                            elif expected_type.lower() == 'str':
                                value = str(value)

                            row_result[key] = {"Label": label, "Value": value, "Type": expected_type}
                        except Exception as e:
                            row_result[key] = {"Label": label, "Value": f"error: {str(e)}", "Type": "error"}
                    else:
                        existing = row_result.get(key, {})
                        row_result[key] = {
                            "Label": label,
                            "Value": existing.get("Value"),
                            "Type": existing.get("Type", expected_type)
                        }

            result_data.append(row_result)

        for item in serializer.validated_data['data']:
            for key, val in item.items():
                label = val.get("Label") or key
                expected_type = val.get("Type", "unknown")
                result_schema[key] = {"Label": label, "Type": expected_type}

        return Response({
            "Title": table.title,
            "project": table.project.name,
            "data": result_schema,
            "results": result_data
        })

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })
        return Response(serializer.errors, status=400)

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

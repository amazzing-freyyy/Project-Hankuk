from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
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
from collections import defaultdict
import pandas as pd
import math

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
            entry = copy.deepcopy(serializer.validated_data['data'])
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

def parse_expression(expr):
    """
    Parse expressions like:
      - average(score)
      - sum(score)
      - stddev(score)
      - ln(score)
      - rolling_avg(score, 3)
      - rolling_stddev(score, 5)
      - abs(score)
    Returns function name and list of arguments.
    """
    expr = expr.strip()
    if '(' not in expr or not expr.endswith(')'):
        return expr, []
    func_name, arg_str = expr.split('(', 1)
    func_name = func_name.strip().lower()
    arg_str = arg_str[:-1]  # remove trailing ')'
    args = [a.strip() for a in arg_str.split(',')]
    return func_name, args


class ProcessDataView(APIView):
    permission_classes = [IsCoachOrAdmin]

    def post(self, request):
        serializer = ProcessDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        table = get_object_or_404(DynamicTable, title=serializer.validated_data['Title'])
        if request.user.userprofile.project != table.project:
            return Response({'error': 'No permission'}, status=status.HTTP_403_FORBIDDEN)

        raw_data = DynamicData.objects.filter(table=table)

        # Convert raw_data rows to list of dicts: key -> float value or None
        data_rows = []
        for row_obj in raw_data:
            simple_row = {}
            for k, v in row_obj.row.items():
                try:
                    simple_row[k] = float(v.get('value'))
                except Exception:
                    simple_row[k] = None
            data_rows.append(simple_row)

        if not data_rows:
            return Response({'error': 'No data found in table'}, status=status.HTTP_400_BAD_REQUEST)

        df = pd.DataFrame(data_rows)

        # Prepare result columns
        for key, val in serializer.validated_data['data'].items():
            label = val.get("Label") or key
            expr = val.get("Expression")
            expected_type = val.get("Type", "unknown")

            if expr:
                func_name, args = parse_expression(expr)

                if func_name == "average" and len(args) == 1:
                    df[key] = df[args[0]].mean()
                elif func_name == "sum" and len(args) == 1:
                    df[key] = df[args[0]].sum()
                elif func_name == "stddev" and len(args) == 1:
                    df[key] = df[args[0]].std()
                elif func_name == "ln" and len(args) == 1:
                    df[key] = df[args[0]].apply(lambda x: math.log(x) if x is not None and x > 0 else None)
                elif func_name == "rolling_avg" and len(args) >= 1:
                    window = int(args[1]) if len(args) > 1 else 3
                    df[key] = df[args[0]].rolling(window=window).mean()
                elif func_name == "rolling_stddev" and len(args) >= 1:
                    window = int(args[1]) if len(args) > 1 else 3
                    df[key] = df[args[0]].rolling(window=window).std()
                elif func_name == 'abs' and len(args) == 1:
                    df[key] = df[args[0]].abs()
                else:
                    # Fallback: try pandas eval for more complex expressions
                    try:
                        # Replace function names with pandas equivalents if needed
                        # or simply try evaluating expression directly on df
                        df[key] = df.eval(expr)
                    except Exception as e:
                        return Response({'error': f'Failed to evaluate expression "{expr}": {str(e)}'},
                                        status=status.HTTP_400_BAD_REQUEST)
            else:
                # If no expression, keep existing or fill with NaN
                df[key] = None

        # Build the result_data for response
        result_data = []
        for _, row in df.iterrows():
            row_result = {}
            for col in df.columns:
                row_result[col] = {
                    "Label": serializer.validated_data['data'].get(col, {}).get("Label", col),
                    "value": row[col] if not pd.isna(row[col]) else None,
                    "Type": serializer.validated_data['data'].get(col, {}).get("Type", "unknown"),
                }
            result_data.append(row_result)

        # Update schema to include new keys
        result_schema = copy.deepcopy(table.schema)
        for key, val in serializer.validated_data['data'].items():
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

class FormViewSet(viewsets.ModelViewSet):
    serializer_class = FormSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsCoachOrAdmin()]
        return [IsInProject()]

    def get_queryset(self):
        user_project = self.request.user.userprofile.project
        return Form.objects.filter(project=user_project)

    def perform_create(self, serializer):
        serializer.save(project=self.request.user.userprofile.project)
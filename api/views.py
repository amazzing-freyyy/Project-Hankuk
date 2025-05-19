from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Project, DynamicTable, DynamicData
from .serializers import *
from .permissions import *
from django.shortcuts import get_object_or_404
from uuid import uuid4
import copy, operator, math

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
                DynamicData.objects.create(table=table, row=entry)
            return Response({'message': 'Data submitted'})
        return Response(serializer.errors, status=400)

class GetTableDataView(APIView):
    def get(self, request, title):
        table = get_object_or_404(DynamicTable, title=title)
        if request.user.userprofile.project != table.project:
            return Response({'error': 'No permission'}, status=403)
        data = [entry.row for entry in DynamicData.objects.filter(table=table)]
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
                        row.row[key].update(val)
                        row.save()
            return Response({'message': 'Data updated'})
        return Response(serializer.errors, status=400)

class ProcessDataView(APIView):
    permission_classes = [IsCoachOrAdmin]

    def post(self, request):
        serializer = ProcessDataSerializer(data=request.data)
        if serializer.is_valid():
            table = get_object_or_404(DynamicTable, title=serializer.validated_data['Title'])
            if request.user.userprofile.project != table.project:
                return Response({'error': 'No permission'}, status=403)

            result_schema = copy.deepcopy(table.schema)
            result_data = []
            raw_data = DynamicData.objects.filter(table=table)

            for row_obj in raw_data:
                row_result = copy.deepcopy(row_obj.row)
                for key, val in serializer.validated_data['data'].items():
                    label = val.get("Label") or key
                    expr = val.get("Expression")
                    if expr:
                        try:
                            local_env = {k: float(v['Value']) for k, v in row_result.items() if 'Value' in v}
                            value = eval(expr, {"__builtins__": {}}, local_env)
                            row_result[key] = {"Label": label, "Value": value, "Type": "processed"}
                        except Exception as e:
                            row_result[key] = {"Label": label, "Value": f"error: {str(e)}", "Type": "error"}
                    else:
                        row_result[key] = {"Label": label, **row_result.get(key, {})}
                result_data.append(row_result)

            for key, val in serializer.validated_data['data'].items():
                label = val.get("Label") or key
                result_schema[key] = {"Label": label, "Type": "processed"}

            return Response({"Title": table.title, "project": table.project.name, "data": result_schema, "results": result_data})
        return Response(serializer.errors, status=400)
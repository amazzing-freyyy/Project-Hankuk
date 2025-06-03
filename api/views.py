# views.py
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import *
from .serializers import *
from .permissions import *
from asteval import Interpreter

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        if self.request.user.is_admin:
            return self.queryset
        return self.queryset.filter(users=self.request.user)

class FormSchemaViewSet(viewsets.ModelViewSet):
    queryset = FormSchema.objects.all()
    serializer_class = FormSchemaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(project__users=self.request.user)

class FormSubmissionViewSet(viewsets.ModelViewSet):
    queryset = FormSubmission.objects.all()
    serializer_class = FormSubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_athlete:
            return Response({"error": "Only athletes can submit"}, status=403)
        form = serializer.validated_data['form']
        project = form.project
        if self.request.user in project.users.filter(is_athlete=True):
            serializer.save(user=self.request.user)
    
    def validate_data(self, value):
        form = self.initial_data.get('form')
        if not form:
            raise serializers.ValidationError("Form ID is required.")

        try:
            form_obj = FormSchema.objects.get(id=form)
        except FormSchema.DoesNotExist:
            raise serializers.ValidationError("Form schema does not exist.")

        schema = form_obj.schema

        errors = {}
        for key, field_def in schema.items():
            field_type = field_def.get("type")
            required = field_def.get("required", False)

            if required and key not in value:
                errors[key] = "This field is required."
                continue

            if key in value:
                v = value[key]
                try:
                    if field_type == "int":
                        int(v)
                    elif field_type == "float":
                        float(v)
                    elif field_type == "str":
                        str(v)
                    elif field_type == "bool":
                        if not isinstance(v, bool):
                            raise ValueError()
                    else:
                        errors[key] = f"Unsupported field type: {field_type}"
                except ValueError:
                    errors[key] = f"Expected type {field_type}"

        if errors:
            raise serializers.ValidationError(errors)

        return value

    def validate(self, attrs):
        form = attrs.get('form')
        user = self.context['request'].user

        # Validate user belongs to form.project
        if user not in form.project.users.all():
            raise serializers.ValidationError("You are not authorized to submit this form.")

        # Validate user is athlete (if needed)
        if not user.is_athlete:
            raise serializers.ValidationError("Only athletes can submit this form.")

        return attrs

class TableConfigViewSet(viewsets.ModelViewSet):
    queryset = TableConfig.objects.all()
    serializer_class = TableConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(project__users=self.request.user)

class GraphConfigViewSet(viewsets.ModelViewSet):
    queryset = GraphConfig.objects.all()
    serializer_class = GraphConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(project__users=self.request.user)

class GraphDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, graph_id):
        graph = GraphConfig.objects.get(id=graph_id)
        if request.user not in graph.project.users.all():
            return Response({"detail": "Unauthorized"}, status=403)

        submissions = FormSubmission.objects.filter(form=graph.form)

        if graph.filters:
            for key, rule in graph.filters.items():
                if isinstance(rule, dict):
                    for op, value in rule.items():
                        if op == "gte":
                            submissions = submissions.filter(**{f"data__{key}__gte": value})
                        elif op == "lte":
                            submissions = submissions.filter(**{f"data__{key}__lte": value})
                        elif op == "eq":
                            submissions = submissions.filter(**{f"data__{key}": value})

        aeval = Interpreter()
        results = []

        for submission in submissions:
            context = submission.data.copy()

            if graph.computed_fields:
                for field_name, expr in graph.computed_fields.items():
                    try:
                        aeval.symtable = context.copy()
                        context[field_name] = aeval(expr)
                    except:
                        context[field_name] = None

            results.append({
                "x": context.get(graph.x_field),
                "y": context.get(graph.y_field),
                "submitted_at": submission.submitted_at
            })

        return Response(results)

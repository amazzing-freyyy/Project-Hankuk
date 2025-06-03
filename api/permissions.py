# permissions.py
from rest_framework.permissions import BasePermission
from .models import Project

class IsProjectCoach(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.project.users.filter(is_coach=True)

class IsProjectAthlete(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user in obj.project.users.filter(is_athlete=True)

class IsProjectCoachOrReadOnlyGraph(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user in obj.project.users.all()
        return request.user in obj.project.users.filter(is_coach=True)

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


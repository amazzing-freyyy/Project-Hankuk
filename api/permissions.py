from rest_framework.permissions import BasePermission

class IsInProject(BasePermission):
    def has_object_permission(self, request, view, obj):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.project == obj.project

class IsCoachOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['coach', 'admin']

class IsAthleteOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['athlete', 'admin']

# New permission for athlete, coach or admin
class IsAthleteCoachOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'userprofile') and request.user.userprofile.role in ['athlete', 'coach', 'admin']

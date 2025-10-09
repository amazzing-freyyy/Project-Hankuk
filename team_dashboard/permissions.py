from rest_framework.permissions import BasePermission

class IsCoachOrOwner(BasePermission):
    """
    Allows access only to coaches or owner athlete.
    """

    def has_object_permission(self, request, view, obj):
        is_coach = request.user.groups.filter(name='coaches').exists()
        try:
            if type(obj) == 'User':
                is_owner = obj == request.user
            else:
                is_owner = obj.user == request.user
        except AttributeError as e:
            is_owner = obj == request.user
        return is_coach or is_owner
    
class IsCoachOrOwner(BasePermission):
    """
    Allows access only to coaches or owner athlete.
    """

    def has_object_permission(self, request, view, obj):
        is_coach = request.user.groups.filter(name='coaches').exists()
        try:
            if type(obj) == 'User':
                is_owner = obj == request.user
            else:
                is_owner = obj.user == request.user
        except AttributeError as e:
            is_owner = obj == request.user
        return is_coach or is_owner

class IsCoach(BasePermission):
    """
    Allows access only to coaches.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='coaches').exists()
        )
    
class IsAdmin(BasePermission):
    """
    Allows access only to admin.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='coaching_staff').exists()
        )
    
class IsOwner(BasePermission):
    """
    Allows access only to the owner of the object.
    """

    def has_object_permission(self, request, view, obj):
        try:
            if type(obj) == 'User':
                return obj == request.user
            return obj.user == request.user
        except AttributeError as e:
            return obj == request.user

# class IsInGroup(BasePermission):
#     def __init__(self, group_name):
#         self.group_name = group_name

#     def has_permission(self, request, view):
#         return (
#             request.user and
#             request.user.is_authenticated and
#             request.user.groups.filter(name=self.group_name).exists()
#         )
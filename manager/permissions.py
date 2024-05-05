from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow users with admin_role to create a project.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.admin_role

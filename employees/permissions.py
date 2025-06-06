from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Только администратор может создавать, обновлять или удалять объекты.
    Просмотр доступен всем пользователям.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

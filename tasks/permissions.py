from rest_framework import permissions


class IsTaskAssigneeOrAdmin(permissions.BasePermission):
    """
    Права доступа:
    Разрешает доступ к задаче только назначенному пользователю или администратору.
    """

    def has_object_permission(self, request, view, obj):
        """
        Определяет, имеет ли пользователь право доступа к конкретному объекту (задаче).

        Аргументы:
            request: Объект запроса.
            view: Представление, которое обрабатывает запрос.
            obj: Объект, к которому запрашивается доступ (Task).

        Возвращаем:
            True, если у пользователя есть право доступа, иначе False.
        """
        # Разрешаем чтение всем пользователям
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем доступ только назначенному пользователю или администратору
        return obj.assignee == request.user or request.user.is_staff

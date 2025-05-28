from django.urls import path, include
from rest_framework import routers
from .views import TaskViewSet, BusyEmployeesView, ImportantTasksView

router = routers.DefaultRouter()
router.register(r"", TaskViewSet)  # URL для задач

urlpatterns = [
    path("", include(router.urls)),
    path("busy_employees/", BusyEmployeesView.as_view(), name="busy_employees"),
    path("important_tasks/", ImportantTasksView.as_view(), name="important_tasks"),
    path(
        "tasks/<int:pk>/complete/",
        TaskViewSet.as_view({"post": "complete"}),
        name="task-complete",
    ),
]

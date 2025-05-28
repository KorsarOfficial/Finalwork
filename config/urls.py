from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from employees.views import EmployeeViewSet
from tasks.views import TaskViewSet, BusyEmployeesView, ImportantTasksView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Task Tracker API",
        default_version="v1",
        description="API для управления задачами сотрудников",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r"employees", EmployeeViewSet)
router.register(r"tasks", TaskViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/employees/", include("employees.urls")),
    path("api/tasks/", include("tasks.urls")),
    path('api/users/', include(('users.urls', 'users'), namespace='users')),
    path("api/", include(router.urls)),
    path("api/busy_employees/", BusyEmployeesView.as_view(), name="busy_employees"),
    path("api/important_tasks/", ImportantTasksView.as_view(), name="important_tasks"),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

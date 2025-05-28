from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import UserCreateAPIView

app_name = UsersConfig.name

router = SimpleRouter()

urlpatterns = [
    path("", include(router.urls)),
    path("register/", UserCreateAPIView.as_view(),
         name="register"),
    path("login/", TokenObtainPairView.as_view(),
         name="login"),
    path("token/refresh/", TokenRefreshView.as_view(),
         name="token_refresh"),
] + router.urls

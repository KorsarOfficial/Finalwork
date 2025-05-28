from django.core.management import BaseCommand

from users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = User.objects.create(email="05bat@mail.ru")
        users.set_password("0353")
        users.is_staff = True
        users.is_active = True
        users.is_superuser = True
        users.save()

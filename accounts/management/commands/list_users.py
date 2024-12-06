from django.core.management.base import BaseCommand
from accounts.models import User  # Substitua pelo modelo que você está usando

class Command(BaseCommand):
    help = 'Lista todos os usuários registrados'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        for user in users:
            self.stdout.write(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, CPF: {getattr(user, 'cpf', 'N/A')}")

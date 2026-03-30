from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


UserModel = get_user_model()


class MatriculeEmailBackend(ModelBackend):
    """Authentification à l'aide du numéro matricul, de l'adresse e-mail ou du nom d'utilisateur."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel.objects.filter(username__iexact=username).first()
            if not user and '@' in username:
                user = UserModel.objects.filter(email__iexact=username).first()
            if not user:
                user = UserModel.objects.filter(matricule__iexact=username).first()
            if user and user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None
        return None

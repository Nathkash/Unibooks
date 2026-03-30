from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    """Option force_password_change, rediriger vers la page de changement de mot de passe."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            if getattr(user, 'force_password_change', False):
                path = request.path
                if path.startswith('/admin/'):
                    return self.get_response(request)

                if '/password-change/' in path or path.endswith('/logout/') or '/logout/' in path:
                    return self.get_response(request)

                return redirect('student:password_change')
        return self.get_response(request)


class SubscriptionMiddleware:
    """Si l'abonnement d'un utilisateur a expiré, déconnecter."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        path = request.path
        if path.startswith('/admin/'):
            return self.get_response(request)
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/subscription_required') or path.startswith('/subscription-required'):
            return self.get_response(request)

        if user and user.is_authenticated and not user.is_staff:
            if getattr(user, 'date_paiement', None) and not getattr(user, 'subscription_is_active', False):
                from django.contrib.auth import logout
                from django.shortcuts import render
                logout(request)
                return render(request, 'student/subscription_required.html', {'profile_user': user})

        return self.get_response(request)

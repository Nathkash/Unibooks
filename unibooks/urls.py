from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from library import views as library_views
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    # compatibility redirect for old custom admin path
    path('library-admin/', RedirectView.as_view(url='/admin/', permanent=False)),
    # compatibility landing pages for legacy '/student/...' URLs — show a friendly message
    # and then redirect to the new canonical routes. This looks nicer than an immediate 302.
    path('student/login/', TemplateView.as_view(
        template_name='compat/student_redirect.html',
        extra_context={'target_url': '/login/', 'target_name': 'Connexion', 'seconds': 4}
    )),
    path('student/dashboard/', TemplateView.as_view(
        template_name='compat/student_redirect.html',
        extra_context={'target_url': '/dashboard/', 'target_name': 'Tableau de bord', 'seconds': 4}
    )),
    path('student/password_change/', TemplateView.as_view(
        template_name='compat/student_redirect.html',
        extra_context={'target_url': '/password_change/', 'target_name': 'Changer le mot de passe', 'seconds': 4}
    )),
    path('student/subscription_required/', TemplateView.as_view(
        template_name='compat/student_redirect.html',
        extra_context={'target_url': '/subscription_required/', 'target_name': 'Abonnement requis', 'seconds': 4}
    )),
    # root home: redirect to dashboard if logged in, else to login
    path('', library_views.home, name='home'),
    # student-facing URLs available at root (e.g. /login/, /books/)
    path('', include(('library.urls_student', 'library'), namespace='student')),
    # NOTE: removed the duplicate inclusion under '/student/' to avoid namespace ambiguity
]

# Serve media files during development. Some PaaS (like Railway) do not serve
# uploaded MEDIA files by default; for quick deployments we allow enabling
# media serving in production by setting the env var DJANGO_SERVE_MEDIA=1.
if settings.DEBUG or os.environ.get('DJANGO_SERVE_MEDIA') == '1':
    # Add a fallback route for media to try serving similar filenames when exact
    # matches are missing (helps with variant names created during upload).
    urlpatterns.insert(0, path('media/<path:path>', library_views.media_fallback))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

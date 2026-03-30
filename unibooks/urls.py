"""
URL configuration for unibooks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from library import views as library_views
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path('healthz', library_views.health),
    path('admin/', admin.site.urls),
    path('library-admin/', RedirectView.as_view(url='/admin/', permanent=False)),
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
    path('', library_views.home, name='home'),
    path('', include(('library.urls_student', 'library'), namespace='student')),
]

if settings.DEBUG or os.environ.get('DJANGO_SERVE_MEDIA') == '1':
    urlpatterns.insert(0, path('media/<path:path>', library_views.media_fallback))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

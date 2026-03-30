from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from .forms import StudentLoginForm, ForcePasswordChangeForm, MissingRequestForm
from .models import Book, BorrowRequest, Reservation, Like, Comment, Notification, ActionLog
from django.utils import timezone
from django.http import HttpResponse
from django.http import FileResponse, Http404, HttpResponseNotFound
import mimetypes
import os
from django.conf import settings


def media_fallback(request, path):
    """Diffuser les fichiers multimédias avec une recherche de repli lorsque le nom de fichier exact est manquant.(IA)"""
    import logging
    logger = logging.getLogger('library.media_fallback')

    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        mime, _ = mimetypes.guess_type(full_path)
        return FileResponse(open(full_path, 'rb'), content_type=mime or 'application/octet-stream')

    # Essayez une solution de repli dans le même répertoire avec plusieurs heuristiques.
    dir_name, filename = os.path.split(path)
    basename, ext = os.path.splitext(filename)

    def norms(s):
        # donner quelques variantes normalisées de s
        yield s
        try:
            import unicodedata
            nf = unicodedata.normalize('NFKD', s)
            yield nf
            # supprimer les signes diacritiques
            stripped = ''.join(c for c in nf if not unicodedata.combining(c))
            yield stripped
        except Exception:
            pass
        # remplacements courants
        yield s.replace(' ', '_')
        yield s.replace(' ', '-')
        yield s.replace("'", '')
        yield s.lower()

    def strip_suffix_tokens(name):
        # supprimer les motifs de jetons courts de fin comme _TWkZG3C ou -gHXIxeS
        import re
        return re.sub(r'[_-][A-Za-z0-9]{4,}$', '', name)

    search_dir = os.path.join(settings.MEDIA_ROOT, dir_name)
    candidates = []

    if os.path.isdir(search_dir):
        try:
            files = os.listdir(search_dir)
        except OSError:
            files = []

        # Première passe : essayer des correspondances exactes normalisées (sensibles et insensibles à la casse)
        norm_targets = set()
        for n in norms(basename):
            norm_targets.add(n + ext)
            norm_targets.add((n + ext).lower())

        for f in files:
            if f in norm_targets or f.lower() in {t.lower() for t in norm_targets}:
                candidates.append(f)

        # Deuxième passe : essayer de supprimer les jetons de suffixe
        if not candidates:
            stripped = strip_suffix_tokens(basename)
            if stripped != basename:
                for f in files:
                    if f.startswith(stripped):
                        candidates.append(f)

        # Troisième passe : correspondance de sous-chaîne (basename contenu dans le nom de fichier) - moins strict
        if not candidates:
            for f in files:
                if basename.lower() in f.lower():
                    candidates.append(f)

    if candidates:
        # privilégier le candidat qui ressemble le plus (heuristique de modification la plus courte)
        chosen = sorted(candidates, key=lambda x: abs(len(x) - len(filename)))[0]
        chosen_path = os.path.join(search_dir, chosen)
        logger.info('media_fallback: serving %s for requested %s', chosen_path, path)
        mime, _ = mimetypes.guess_type(chosen_path)
        return FileResponse(open(chosen_path, 'rb'), content_type=mime or 'application/octet-stream')

        logger.info('media_fallback: no candidate found for %s', path)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300">
    <rect width="100%" height="100%" fill="#eeeeee"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#777" font-family="Arial,Helvetica,sans-serif" font-size="16">No cover</text>
    <text x="50%" y="65%" dominant-baseline="middle" text-anchor="middle" fill="#999" font-family="Arial,Helvetica,sans-serif" font-size="10">{os.path.basename(path)}</text>
</svg>'''
        return HttpResponse(svg, content_type='image/svg+xml')


def health(request):
    return HttpResponse('OK', content_type='text/plain')


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StudentLoginView(LoginView):
    template_name = 'student/login.html'
    authentication_form = StudentLoginForm
    
    def form_valid(self, form):
        user = form.get_user()
        if hasattr(user, 'date_paiement') and user.date_paiement and not getattr(user, 'subscription_is_active', False):
            return render(self.request, 'student/subscription_required.html', {'profile_user': user})
        return super().form_valid(form)


def home(request):
    """Point d'entrée de la page d'accueil."""
    if request.user.is_authenticated:
        return redirect('student:dashboard')
    return redirect('student:login')


def student_logout(request):
    logout(request)
    return redirect('student:login')


class StudentPasswordChangeView(PasswordChangeView):
    template_name = 'student/password_change.html'
    form_class = ForcePasswordChangeForm
    success_url = reverse_lazy('student:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        user.force_password_change = False
        user.save()
        update_session_auth_hash(self.request, form.user)
        ActionLog = __import__('library.models', fromlist=['ActionLog']).ActionLog
        ActionLog.objects.create(actor=user, action='Password changed')
        messages.success(self.request, 'Mot de passe changé avec succès.')
        return response


@login_required
@ensure_csrf_cookie
def dashboard(request):
    user = request.user
    borrows = user.borrow_requests.all()
    reservations = user.reservations.all()
    notifs = user.notifications.order_by('-created_at')[:10]
    books = Book.objects.order_by('-id')[:8]
    SiteInfo = __import__('library.models', fromlist=['SiteInfo']).SiteInfo
    site_info = SiteInfo.objects.order_by('-updated_at').first()
    return render(request, 'student/dashboard.html', {
        'borrows': borrows,
        'reservations': reservations,
        'notifications': notifs,
        'books': books,
        'site_info': site_info,
    })


@login_required
@ensure_csrf_cookie
def book_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status')
    books = Book.objects.all()
    if q:
        books = books.filter(title__icontains=q) | books.filter(authors__icontains=q)
    if status == 'available':
        books = books.filter(available_copies__gt=0)
    elif status == 'unavailable':
        books = books.filter(available_copies__lte=0)
    return render(request, 'student/book_list.html', {'books': books})


@login_required
def my_borrows(request):
    """Page listant les emprunts de l'utilisateur"""
    borrows = request.user.borrow_requests.order_by('-requested_at')
    return render(request, 'student/borrows.html', {'borrows': borrows})


@login_required
def my_reservations(request):
    """Page listant les réservations de l'utilisateur"""
    reservations = request.user.reservations.order_by('-reserved_at')
    return render(request, 'student/reservations.html', {'reservations': reservations})


@login_required
@ensure_csrf_cookie
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user = request.user
    liked = Like.objects.filter(student=user, book=book).exists()
    comments = book.comments.filter(parent__isnull=True).order_by('-created_at')
    return render(request, 'student/book_detail.html', {'book': book, 'liked': liked, 'comments': comments})


@login_required
def request_borrow(request, pk):
    book = get_object_or_404(Book, pk=pk)
    BorrowRequest.objects.create(student=request.user, book=book)
    ActionLog = __import__('library.models', fromlist=['ActionLog']).ActionLog
    ActionLog.objects.create(actor=request.user, action=f'Requested borrow for {book.pk}')
    messages.success(request, 'Demande d\'emprunt soumise.')
    return redirect('student:book_detail', pk=pk)


@login_required
def request_reserve(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.available_copies > 0:
        messages.error(request, 'Le livre est disponible, pas besoin de réserver.')
        return redirect('student:book_detail', pk=pk)
    Reservation.objects.create(student=request.user, book=book)
    ActionLog = __import__('library.models', fromlist=['ActionLog']).ActionLog
    ActionLog.objects.create(actor=request.user, action=f'Reserved book {book.pk}')
    messages.success(request, 'Réservation enregistrée.')
    return redirect('student:book_detail', pk=pk)


@login_required
@ensure_csrf_cookie
def missing_request(request):
    if request.method == 'POST':
        form = MissingRequestForm(request.POST)
        if form.is_valid():
            mr = form.save(commit=False)
            mr.student = request.user
            mr.save()
            messages.success(request, 'Demande enregistrée.')
            return redirect('student:dashboard')
    else:
        form = MissingRequestForm()
    return render(request, 'student/missing_request.html', {'form': form})


@login_required
@ensure_csrf_cookie
def notifications(request):
    try:
        request.user.notifications.filter(read=False).update(read=True)
    except Exception:
        pass

    notifs = request.user.notifications.order_by('-created_at')
    return render(request, 'student/notifications.html', {'notifications': notifs})


@login_required
def like_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    like, created = Like.objects.get_or_create(student=request.user, book=book)
    if not created:
        like.delete()
        messages.info(request, 'Like retiré')
    else:
        messages.success(request, 'Livre aimé')
    return redirect('student:book_detail', pk=pk)


@login_required
def comment_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    content = request.POST.get('content')
    parent_id = request.POST.get('parent')
    parent = None
    if parent_id:
        parent = Comment.objects.filter(pk=parent_id).first()
    if content:
        Comment.objects.create(student=request.user, book=book, parent=parent, content=content)
        messages.success(request, 'Commentaire ajouté')
    return redirect('student:book_detail', pk=pk)


@login_required
def profile(request):
    """Afficher la page de profil de l'utilisateur (lecture seule)."""
    user = request.user

    if request.method == 'POST':
        if request.POST.get('remove_avatar'):
            if getattr(user, 'avatar', None):
                try:
                    user.avatar.delete(save=False)
                except Exception:
                    pass
            user.avatar = None
            user.save()
            messages.info(request, 'Photo de profil supprimée.')
            return redirect('student:profile')

        if request.FILES.get('avatar'):
            avatar_file = request.FILES.get('avatar')
            user.avatar = avatar_file
            user.save()
            messages.success(request, 'Photo de profil mise à jour.')
            return redirect('student:profile')

    if not user.is_active:
        account_status = {'label': '⛔ Désactivé', 'code': 'disabled'}
    elif user.force_password_change:
        account_status = {'label': '⚠️ Mot de passe par défaut', 'code': 'force_change', 'blocked': True}
    else:
        account_status = {'label': '✅ Actif', 'code': 'active'}

    # Abonnement / droits de bibliothèque
    allowed_borrows = 5
    active_borrows_count = BorrowRequest.objects.filter(student=user, status='APPROVED').count()
    remaining_borrows = max(0, allowed_borrows - active_borrows_count)

    # Activité récente
    borrows_recent = list(user.borrow_requests.order_by('-requested_at')[:5])
    reservations_recent = list(user.reservations.order_by('-reserved_at')[:5])
    comments_recent = list(Comment.objects.filter(student=user).order_by('-created_at')[:5])

    activities = []
    for b in borrows_recent:
        activities.append({'type': 'emprunt', 'when': getattr(b, 'requested_at', timezone.now()), 'text': f"Demande d'emprunt: {b.book.title}", 'obj': b})
    for r in reservations_recent:
        activities.append({'type': 'réservation', 'when': getattr(r, 'reserved_at', timezone.now()), 'text': f"Réservation: {r.book.title}", 'obj': r})
    for c in comments_recent:
        activities.append({'type': 'commentaire', 'when': getattr(c, 'created_at', timezone.now()), 'text': f"Commentaire sur: {c.book.title}", 'obj': c})

    activities = sorted(activities, key=lambda x: x['when'], reverse=True)[:5]

    sub_start = getattr(user, 'date_paiement', None)
    sub_end = getattr(user, 'date_expiration', None) or (user.compute_expiration() if hasattr(user, 'compute_expiration') else None)
    if sub_end:
        delta = sub_end - timezone.now()
        subscription_days_left = max(0, delta.days)
    else:
        subscription_days_left = None

    context = {
        'profile_user': user,
        'account_status': account_status,
        'date_paiement': sub_start,
        'date_expiration': sub_end,
        'subscription_active': getattr(user, 'subscription_is_active', False),
        'subscription_days_left': subscription_days_left,
        'allowed_borrows': allowed_borrows,
        'active_borrows_count': active_borrows_count,
        'remaining_borrows': remaining_borrows,
        'activities': activities,
    }
    return render(request, 'student/profile.html', context)


def subscription_required(request):
    """Page d'information exipiration d'abonnement."""
    profile_user = None
    if request.user.is_authenticated:
        profile_user = request.user

    subscription_end = None
    subscription_days_left = None
    subscription_status = None
    if profile_user and getattr(profile_user, 'date_paiement', None):
        subscription_end = profile_user.date_expiration or (profile_user.compute_expiration() if hasattr(profile_user, 'compute_expiration') else None)
        if subscription_end:
            delta = subscription_end - timezone.now()
            subscription_days_left = max(0, delta.days)
            if subscription_end < timezone.now():
                subscription_status = 'Expiré'
            else:
                subscription_status = 'Actif'
        else:
            subscription_status = 'Inconnu'

    return render(request, 'student/subscription_required.html', {
        'profile_user': profile_user,
        'subscription_end': subscription_end,
        'subscription_days_left': subscription_days_left,
        'subscription_status': subscription_status,
    })


def health(request):
    """Simple health check endpoint for PaaS health probes."""
    return HttpResponse('OK', content_type='text/plain')

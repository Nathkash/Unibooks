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


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StudentLoginView(LoginView):
    template_name = 'student/login.html'
    authentication_form = StudentLoginForm
    
    def form_valid(self, form):
        # Before logging in, check subscription status. If expired, show a friendly page
        user = form.get_user()
        # If user has a payment date but subscription expired, render subscription_required
        if hasattr(user, 'date_paiement') and user.date_paiement and not getattr(user, 'subscription_is_active', False):
            # Do not log the user in; present a page explaining how to subscribe at the library
            return render(self.request, 'student/subscription_required.html', {'profile_user': user})
        return super().form_valid(form)


def home(request):
    """Home entrypoint: redirect to dashboard if authenticated, else to login."""
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
        # unset force flag
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
    # include a small list of recently added books for the dashboard
    books = Book.objects.order_by('-id')[:8]
    # Site-wide info editable in admin
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
    # create borrow request; admin will validate
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
    # Mark unread notifications as read when the user visits the notifications page
    try:
        request.user.notifications.filter(read=False).update(read=True)
    except Exception:
        # If for some reason the relation or DB is not ready, ignore and continue
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
    """Affiche la page de profil de l'utilisateur (lecture seule)."""
    user = request.user

    # Allow the user to upload/update their avatar from this page
    if request.method == 'POST':
        # Remove avatar request (button)
        if request.POST.get('remove_avatar'):
            if getattr(user, 'avatar', None):
                try:
                    # delete the file from storage
                    user.avatar.delete(save=False)
                except Exception:
                    # ignore deletion errors; still clear the field
                    pass
            user.avatar = None
            user.save()
            messages.info(request, 'Photo de profil supprimée.')
            return redirect('student:profile')

        # Upload new avatar (file input auto-submits on change)
        if request.FILES.get('avatar'):
            avatar_file = request.FILES.get('avatar')
            user.avatar = avatar_file
            user.save()
            messages.success(request, 'Photo de profil mise à jour.')
            return redirect('student:profile')

    # Account status determination
    if not user.is_active:
        account_status = {'label': '⛔ Désactivé', 'code': 'disabled'}
    elif user.force_password_change:
        account_status = {'label': '⚠️ Mot de passe par défaut', 'code': 'force_change', 'blocked': True}
    else:
        account_status = {'label': '✅ Actif', 'code': 'active'}

    # Subscription / library rights (lightweight defaults)
    # We don't have a subscription model; show placeholders and compute borrow allowance from simple policy.
    allowed_borrows = 5
    active_borrows_count = BorrowRequest.objects.filter(student=user, status='APPROVED').count()
    remaining_borrows = max(0, allowed_borrows - active_borrows_count)

    # Recent activity: mix of borrow requests, reservations and comments
    borrows_recent = list(user.borrow_requests.order_by('-requested_at')[:5])
    reservations_recent = list(user.reservations.order_by('-reserved_at')[:5])
    comments_recent = list(Comment.objects.filter(student=user).order_by('-created_at')[:5])

    # Merge and sort by timestamp (approx)
    activities = []
    for b in borrows_recent:
        activities.append({'type': 'emprunt', 'when': getattr(b, 'requested_at', timezone.now()), 'text': f"Demande d'emprunt: {b.book.title}", 'obj': b})
    for r in reservations_recent:
        activities.append({'type': 'réservation', 'when': getattr(r, 'reserved_at', timezone.now()), 'text': f"Réservation: {r.book.title}", 'obj': r})
    for c in comments_recent:
        activities.append({'type': 'commentaire', 'when': getattr(c, 'created_at', timezone.now()), 'text': f"Commentaire sur: {c.book.title}", 'obj': c})

    activities = sorted(activities, key=lambda x: x['when'], reverse=True)[:5]

    # subscription days left
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
        # Subscription info
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
    """Simple informational page shown when a user's subscription has expired.

    This view is also the redirect target for the middleware.
    """
    # If called directly, provide subscription details when possible
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
            # Status: expired if end is in the past
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

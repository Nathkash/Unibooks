from django import template
from django.urls import reverse
from library.models import MissingRequest
from library.models import BorrowRequest, Reservation

register = template.Library()


@register.simple_tag
def unhandled_missing_count():
    """Renvoie le nombre d'objets MissingRequest non encore traités."""
    return MissingRequest.objects.filter(handled_at__isnull=True).count()


@register.simple_tag
def missingrequest_admin_url():
    """Renvoie l'URL de la liste de changement admin pour MissingRequest."""
    try:
        return reverse('admin:library_missingrequest_changelist')
    except Exception:
        return '#'


@register.simple_tag
def pending_borrow_count():
    """Renvoie le nombre d'objets BorrowRequest qui nécessitent une attention administrative (PENDING)."""
    return BorrowRequest.objects.filter(status='PENDING').count()


@register.simple_tag
def borrowrequest_admin_url():
    try:
        return reverse('admin:library_borrowrequest_changelist')
    except Exception:
        return '#'


@register.simple_tag
def pending_reservation_count():
    """Renvoie le nombre d'objets de réservation qui peuvent nécessiter une attention particulière (ACTIVE)."""
    return Reservation.objects.filter(status='ACTIVE').count()


@register.simple_tag
def reservation_admin_url():
    try:
        return reverse('admin:library_reservation_changelist')
    except Exception:
        return '#'

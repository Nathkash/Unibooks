def unread_notifications(request):
    """Processeur qui injecte le nombre de notifications non lue."""
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            count = user.notifications.filter(read=False).count()
        except Exception:
            count = 0
    else:
        count = 0

    return {
        'unread_notifications_count': count,
        'has_unread_notifications': bool(count),
    }

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from library.models import BorrowRequest, Notification, ActionLog
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Envoyer des rappels pour les emprunts dus ou en retard (peut être exécuté par cron)'

    def handle(self, *args, **options):
        today = timezone.now().date()
        soon = today + timedelta(days=3)
        # due est <=3 days
        due_soon = BorrowRequest.objects.filter(status='APPROVED', due_date__lte=soon, due_date__gte=today)
        overdue = BorrowRequest.objects.filter(status='APPROVED', due_date__lt=today)

        for br in due_soon:
            msg = f'Rappel: votre emprunt pour "{br.book.title}" arrive à échéance le {br.due_date}.'
            Notification.objects.create(recipient=br.student, message=msg, type='reminder')
            try:
                send_mail('Rappel de retour - UniBooks', msg, settings.DEFAULT_FROM_EMAIL, [br.student.email], fail_silently=True)
            except Exception:
                pass
            ActionLog.objects.create(actor=None, action=f'Rappel de retour envoyé pour l\'emprunt {br.pk}')

        for br in overdue:
            msg = f'Attention: votre emprunt pour "{br.book.title}" est en retard depuis le {br.due_date}.'
            Notification.objects.create(recipient=br.student, message=msg, type='overdue')
            try:
                send_mail('Emprunt en retard - UniBooks', msg, settings.DEFAULT_FROM_EMAIL, [br.student.email], fail_silently=True)
            except Exception:
                pass
            ActionLog.objects.create(actor=None, action=f'Rappel de retour envoyé pour l\'emprunt {br.pk}')

        self.stdout.write(self.style.SUCCESS('Rappels envoyés.'))

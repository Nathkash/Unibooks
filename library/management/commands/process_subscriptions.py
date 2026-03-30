from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from library.models import User, Notification, ActionLog
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = "Gestion des abonnements : envoi d’un rappel à 26 jours, expiration à 31 jours"

    def handle(self, *args, **options):
        now = timezone.now()
        users = User.objects.exclude(date_paiement__isnull=True)
        if not users.exists():
            self.stdout.write('Aucun abonnement avec date de paiement trouvé.')
            return

        for u in users:
            if not u.date_paiement:
                continue
            days = (now - u.date_paiement).days

            # Expire après 31 jours
            if days >= 31:
                if u.is_active:
                    u.is_active = False
                    u.save()
                    try:
                        sessions = Session.objects.all()
                        for s in sessions:
                            data = s.get_decoded()
                            if str(data.get('_auth_user_id')) == str(u.pk):
                                s.delete()
                    except Exception:
                        pass

                Notification.objects.create(
                    recipient=u,
                    message="Votre abonnement de 31 jours est arrivé à expiration. Votre accès a été suspendu. Veuillez renouveler au guichet.",
                    type='subscription_expired'
                )
                ActionLog.objects.create(actor=None, action=f"Abonnement à expiration automatique pour {u.username}", extra={'days': days})
                self.stdout.write(self.style.WARNING(f"Expiré: {u.username} (jours={days})"))
                continue

            # Envoyer un rappel au bout de 26 jours
            if 26 <= days < 31:
                window_start = now - timedelta(days=10)
                already = u.notifications.filter(type='subscription_reminder', created_at__gte=window_start).exists()
                if not already:
                    days_left = 31 - days
                    Notification.objects.create(
                        recipient=u,
                        message=f"Rappel : votre abonnement expire dans {days_left} jour(s). Pensez à le renouveler au guichet.",
                        type='subscription_reminder'
                    )
                    ActionLog.objects.create(actor=None, action=f"J'ai envoyé un rappel d'abonnement à {u.username}", extra={'days_left': days_left})
                    self.stdout.write(self.style.SUCCESS(f"Rappel envoyé : {u.username} (jours={days}, jours_restants={days_left})"))
                else:
                    self.stdout.write(f"Rappel déjà envoyé récemment : {u.username}")
                continue

            self.stdout.write(f"Aucune action pour {u.username} (jours={days})")

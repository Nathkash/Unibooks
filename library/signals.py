from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import BorrowRequest, Reservation, Notification, ActionLog
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(pre_save, sender=BorrowRequest)
def borrow_pre_save(sender, instance, **kwargs):
    """Détecter le passage du statut à APPROUVÉ et marquer l'instance pour le travail post-enregistrement."""
    if not instance.pk:
        return
    try:
        old = BorrowRequest.objects.get(pk=instance.pk)
    except BorrowRequest.DoesNotExist:
        return
    if old.status != 'APPROVED' and instance.status == 'APPROVED':
        setattr(instance, '_was_approved', True)


@receiver(post_save, sender=BorrowRequest)
def borrow_post_save(sender, instance, created, **kwargs):
    if created:
        msg = f"Votre demande d'emprunt pour \"{instance.book.title}\" a été reçue et est en attente de validation."
        Notification.objects.create(recipient=instance.student, message=msg, type='info')
        ActionLog.objects.create(actor=instance.student, action=f'Created borrow request {instance.pk}')

    if getattr(instance, '_was_approved', False) or (created and instance.status == 'APPROVED'):
        due = getattr(instance, 'due_date', None)
        borrow_date = getattr(instance, 'borrow_date', None)
        msg = f"Votre emprunt pour \"{instance.book.title}\" a été accepté."
        if borrow_date:
            msg += f" Emprunté le {borrow_date}."
        if due:
            msg += f" Date d'échéance : {due}."
        Notification.objects.create(recipient=instance.student, message=msg, type='borrow_approved')
        # envoyer mail
        try:
            send_mail('Emprunt accepté - UniBooks', msg, settings.DEFAULT_FROM_EMAIL, [instance.student.email], fail_silently=True)
        except Exception:
            pass
        ActionLog.objects.create(actor=None, action=f'Borrow {instance.pk} approved and notification sent')


@receiver(pre_save, sender=Reservation)
def reservation_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Reservation.objects.get(pk=instance.pk)
    except Reservation.DoesNotExist:
        return
    if old.status != instance.status:
        setattr(instance, '_status_changed', True)


@receiver(post_save, sender=Reservation)
def reservation_post_save(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(recipient=instance.student,
                                    message=f"Votre réservation pour \"{instance.book.title}\" a été enregistrée.",
                                    type='info')
        ActionLog.objects.create(actor=instance.student, action=f'Created reservation {instance.pk}')
        return

    if getattr(instance, '_status_changed', False):
        if instance.status == 'FULFILLED':
            Notification.objects.create(recipient=instance.student,
                                        message=f"Votre réservation pour \"{instance.book.title}\" est prête à être récupérée.",
                                        type='reservation_ready')
            ActionLog.objects.create(actor=None, action=f'Reservation {instance.pk} fulfilled; notified student')
        elif instance.status == 'CANCELLED':
            Notification.objects.create(recipient=instance.student,
                                        message=f"Votre réservation pour \"{instance.book.title}\" a été annulée.",
                                        type='reservation_cancelled')
            ActionLog.objects.create(actor=None, action=f'Reservation {instance.pk} cancelled; notified student')



@receiver(post_save, sender='library.MissingRequest')
def missingrequest_post_save(sender, instance, created, **kwargs):
    """Notifier les utilisateurs du personnel/admin lorsque une MissingRequest (demande d'achat) est créée.

    Nous créons une Notification pour chaque utilisateur du personnel et une entrée ActionLog. Nous essayons également
    d'envoyer un e-mail au personnel (au mieux via send_mail).
    """
    if not created:
        return
    msg = f"Nouvelle demande d'achat: \"{instance.title}\" par {instance.student}."

    staff_users = User.objects.filter(is_staff=True)
    for admin in staff_users:
        Notification.objects.create(recipient=admin, message=msg, type='missing_request')

    ActionLog.objects.create(actor=instance.student, action=f'Created MissingRequest {instance.pk}')

    try:
        send_mail('Nouvelle demande d\'achat - UniBooks', msg, settings.DEFAULT_FROM_EMAIL, [u.email for u in staff_users if u.email], fail_silently=True)
    except Exception:
        pass

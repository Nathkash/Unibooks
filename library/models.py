from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


class User(AbstractUser):

    matricule = models.CharField(_('matricule'), max_length=30, unique=True, null=True, blank=True)
    faculty = models.CharField(_('faculté'), max_length=120, blank=True)
    phone = models.CharField(_('téléphone'), max_length=30, blank=True)
    address = models.TextField(_('adresse'), blank=True)
    proof_of_payment = models.FileField(_('preuve de paiement'), upload_to='proofs/', blank=True, null=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    force_changement_mot_de_passe = models.BooleanField(_('forcer changement mot de passe'), default=False)
    est_bibliothécaire = models.BooleanField(_('personnel bibliothèque'), default=False)
    date_paiement = models.DateTimeField(_('date de paiement'), null=True, blank=True, help_text=_('Date et heure du paiement (format UTC)'))
    date_expiration = models.DateTimeField(_('date d\'expiration'), null=True, blank=True, editable=False)

    def compute_expiration(self):
        if not self.date_paiement:
            return None
        return self.date_paiement + timedelta(days=31)

    @property
    def subscription_is_active(self):
        end = self.date_expiration or self.compute_expiration()
        if not end:
            return False
        return timezone.now() < end

    def save(self, *args, **kwargs):
        if self.date_paiement:
            computed = self.compute_expiration()
            self.date_expiration = computed
        else:
            self.date_expiration = None

        if not self.username:
            import uuid
            candidate = f"u{uuid.uuid4().hex[:12]}"
            Model = type(self)
            while Model.objects.filter(username=candidate).exists():
                candidate = f"u{uuid.uuid4().hex[:12]}"
            self.username = candidate

        super().save(*args, **kwargs)

    def __str__(self):
        names = ' '.join(filter(None, [self.first_name, getattr(self, 'post_nom', None), self.last_name])).strip()
        if names:
            if self.matricule:
                return f"{names} ({self.matricule})"
            return names
        if self.email:
            return self.email
        return self.username


class SiteInfo(models.Model):
    conseil_du_jour = models.TextField(_('conseil du jour'), blank=True)
    annonce = models.TextField(_('annonce'), blank=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)

    class Meta:
        verbose_name = _('Bloc Info')
        verbose_name_plural = _('Blocs Info')

    def __str__(self):
        return f"Info (mis à jour {self.updated_at:%Y-%m-%d %H:%M})"


class Book(models.Model):
    title = models.CharField(_('titre'), max_length=255)
    authors = models.CharField(_('auteurs'), max_length=255)
    category = models.CharField(_('catégorie'), max_length=120, blank=True)
    description = models.TextField(_('description'), blank=True)
    total_copies = models.PositiveIntegerField(_('nombre total d\'exemplaires'), default=1)
    available_copies = models.IntegerField(_('exemplaires disponibles'), default=1)
    image = models.ImageField(_('image'), upload_to='books/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = _('Livre')
        verbose_name_plural = _('Livres')

    def __str__(self):
        return f"{self.title} — {self.authors}"

    @property
    def status(self):
        if self.available_copies <= 0:
            return 'indisponible'
        return 'disponible'


class BorrowRequest(models.Model):
    STATUS = [('PENDING', 'En attente'), ('APPROVED', 'Accepté'), ('REJECTED', 'Refusé'), ('RETURNED', 'Rendu')]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('étudiant'), on_delete=models.CASCADE, related_name='borrow_requests')
    book = models.ForeignKey(Book, verbose_name=_('livre'), on_delete=models.CASCADE, related_name='borrow_requests')
    requested_at = models.DateTimeField(_('demandé le'), auto_now_add=True)
    status = models.CharField(_('statut'), max_length=20, choices=STATUS, default='PENDING')
    admin_comment = models.TextField(_('commentaire admin'), blank=True)
    borrow_date = models.DateField(_('date d\'emprunt'), null=True, blank=True)
    due_date = models.DateField(_('date d\'échéance'), null=True, blank=True)

    def __str__(self):
        return f"{self.student} -> {self.book} ({self.status})"
    
    class Meta:
        verbose_name = _('Demande d\'emprunt')
        verbose_name_plural = _('Demandes d\'emprunt')


class Reservation(models.Model):
    STATUS = [('ACTIVE', 'Active'), ('CANCELLED', 'Annulée'), ('FULFILLED', 'Remplie')]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('étudiant'), on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey(Book, verbose_name=_('livre'), on_delete=models.CASCADE, related_name='reservations')
    reserved_at = models.DateTimeField(_('réservé le'), auto_now_add=True)
    status = models.CharField(_('statut'), max_length=20, choices=STATUS, default='ACTIVE')

    def __str__(self):
        return f"{self.student} réserve {self.book} ({self.status})"
    
    class Meta:
        verbose_name = _('Réservation')
        verbose_name_plural = _('Réservations')


class MissingRequest(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('étudiant'), on_delete=models.CASCADE)
    title = models.CharField(_('titre'), max_length=255)
    authors = models.CharField(_('auteurs'), max_length=255, blank=True)
    justification = models.TextField(_('justification'))
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    status = models.CharField(_('statut'), max_length=30, choices=[('OPEN', _('Ouvert')), ('ORDERED', _('Commandé')), ('DENIED', _('Refusé'))], default='OPEN')
    # Champs de suivi pour la gestion administrative
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('traité par'), null=True, blank=True, on_delete=models.SET_NULL, related_name='handled_missing_requests')
    handled_at = models.DateTimeField(_('traité le'), null=True, blank=True)
    handled_note = models.TextField(_('note de traitement'), blank=True)

    def __str__(self):
        return f"Demande: {self.title} par {self.student} — {self.status}"
    
    class Meta:
        verbose_name = _('Demande d\'achat')
        verbose_name_plural = _('Demandes d\'achat')

    @property
    def is_handled(self):
        return bool(self.handled_at)


class Like(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('étudiant'), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, verbose_name=_('livre'), on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    class Meta:
        unique_together = ('student', 'book')
        verbose_name = _('Like')
        verbose_name_plural = _('Likes')


class Comment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('étudiant'), on_delete=models.CASCADE)
    book = models.ForeignKey(Book, verbose_name=_('livre'), on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', verbose_name=_('parent'), null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField(_('contenu'))
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    def __str__(self):
        return f"Commentaire par {self.student} sur {self.book}"
    
    class Meta:
        verbose_name = _('Commentaire')
        verbose_name_plural = _('Commentaires')


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('destinataire'), on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(_('message'))
    type = models.CharField(_('type'), max_length=50, default='info')
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    read = models.BooleanField(_('lu'), default=False)

    def __str__(self):
        return f"Notif to {self.recipient}: {self.type}"
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')


class ActionLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('acteur'), on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(_('action'), max_length=255)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    extra = models.JSONField(_('données supplémentaires'), blank=True, null=True)

    def __str__(self):
        return f"{self.created_at} — {self.actor}: {self.action}"

    class Meta:
        verbose_name = _('Journal d\'actions')
        verbose_name_plural = _('Journaux d\'actions')

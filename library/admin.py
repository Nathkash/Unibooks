from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Book, BorrowRequest, Reservation, MissingRequest, Like, Comment, Notification, ActionLog
from .models import SiteInfo
from django.utils.translation import gettext_lazy as _


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Supprission `username` et travail Uniquement avec des champs humains.
    readonly_fields = ('date_expiration',)

    def _strip_username_from_fieldsets(self, fieldsets):
        """Fonction d'assistance : supprimer « username » de tout tuple de champs fieldset."""
        new = []
        for name, opts in fieldsets:
            fields = list(opts.get('fields', ()))
            fields = [f for f in fields if f != 'username']
            new.append((name, {'fields': tuple(fields)}))
        return tuple(new)

    def get_fieldsets(self, request, obj=None):
        base = list(super().get_fieldsets(request, obj))
        base = list(self._strip_username_from_fieldsets(base))

        # Ajouter de mes informations
        extra = (
            'UniBooks info',
            {'fields': ('matricule', 'faculty', 'phone', 'address', 'proof_of_payment', 'force_password_change', 'is_librarian', 'date_paiement', 'date_expiration')}
        )
        base.append(extra)
        return tuple(base)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'matricule', 'faculty'),
        }),
    )

    list_display = ('full_name', 'email', 'matricule', 'is_active', 'is_librarian', 'subscription_end_display')
    search_fields = ('first_name', 'last_name', 'matricule', 'email', 'phone')

    def full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.email
    full_name.short_description = _('Nom complet')

    def subscription_end_display(self, obj):
        end = getattr(obj, 'date_expiration', None) or (obj.compute_expiration() if hasattr(obj, 'compute_expiration') else None)
        return end.strftime('%Y-%m-%d') if end else '-'
    subscription_end_display.short_description = 'Abonnement se termine'


# Traduction en français
admin.site.site_header = _('Administration UniBooks')
admin.site.site_title = _('UniBooks admin')
admin.site.index_title = _('Bienvenue sur l\'administration UniBooks')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'authors', 'category', 'total_copies', 'available_copies')
    search_fields = ('title', 'authors')


@admin.register(BorrowRequest)
class BorrowRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'status', 'requested_at')
    list_filter = ('status',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'status', 'reserved_at')


@admin.register(MissingRequest)
class MissingRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'status', 'created_at', 'is_handled', 'handled_by', 'handled_at')
    list_filter = ('status', 'created_at',)
    search_fields = ('title', 'student__first_name', 'student__last_name', 'student__matricule', 'student__email')
    actions = ('mark_as_handled',)

    def mark_as_handled(self, request, queryset):
        """Action de l'administrateur permettant de marquer les demandes sélectionnées comme étant traitées par l'utilisateur administrateur actuel."""
        from django.utils import timezone
        count = 0
        for obj in queryset:
            obj.handled_by = request.user
            obj.handled_at = timezone.now()
            obj.save()
            count += 1
        self.message_user(request, f"{count} demande(s) marquée(s) comme traitée(s).")

    mark_as_handled.short_description = 'Marquer la sélection comme traitée'

admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(ActionLog)
@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_at')
    fields = ('conseil_du_jour', 'annonce')
    ordering = ('-updated_at',)

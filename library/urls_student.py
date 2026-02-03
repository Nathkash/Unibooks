from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('login/', views.StudentLoginView.as_view(), name='login'),
    path('logout/', views.student_logout, name='logout'),
    path('password-change/', views.StudentPasswordChangeView.as_view(), name='password_change'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('borrows/', views.my_borrows, name='my_borrows'),
    path('reservations/', views.my_reservations, name='my_reservations'),
    path('profile/', views.profile, name='profile'),
    path('subscription-required/', views.subscription_required, name='subscription_required'),
    # Backwards-compatible alias: accept underscore in URL as well
    path('subscription_required/', views.subscription_required),
    path('health/', views.health, name='health'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('books/<int:pk>/borrow/', views.request_borrow, name='request_borrow'),
    path('books/<int:pk>/reserve/', views.request_reserve, name='request_reserve'),
    path('missing-request/', views.missing_request, name='missing_request'),
    path('notifications/', views.notifications, name='notifications'),
    path('like/<int:pk>/', views.like_book, name='like_book'),
    path('comment/<int:pk>/', views.comment_book, name='comment_book'),
]

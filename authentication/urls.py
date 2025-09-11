"""
Authentication URLs for EU NCP Portal
Enhanced registration and authentication routes
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Custom login view with HSE theming
    path("login/", views.CustomLoginView.as_view(), name="login"),
    # Registration views
    path("register/", views.register_view, name="register"),
    # Alternative class-based view (if preferred)
    # path('register/', views.EnhancedRegisterView.as_view(), name='register'),
    # Password reset views (using Django's built-in views with custom templates)
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            success_url="/accounts/password_reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]

"""
Enhanced Authentication Views for EU NCP Portal
HSE-themed registration and authentication functionality
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django import forms


class EnhancedUserCreationForm(UserCreationForm):
    """Enhanced user creation form with additional fields"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your first name"}
        ),
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your last name"}
        ),
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email address"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes and placeholders to form fields
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Choose a username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Create a secure password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm your password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


def register_view(request):
    """Enhanced registration view with HSE styling"""
    if request.method == "POST":
        form = EnhancedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")

            # Log the user in automatically after registration
            user = authenticate(
                username=username, password=form.cleaned_data["password1"]
            )
            if user:
                login(request, user)
                messages.success(
                    request,
                    f"Welcome to EU NCP Portal, {user.first_name}! Your account has been created successfully.",
                )
                # Redirect to the next page or home
                next_page = request.GET.get("next", "/")
                return redirect(next_page)
            else:
                messages.success(
                    request,
                    "Your account has been created successfully! Please log in.",
                )
                return redirect("login")
        else:
            messages.error(request, "Please correct the errors below and try again.")
    else:
        form = EnhancedUserCreationForm()

    return render(
        request,
        "registration/register.html",
        {"form": form, "title": "Register - EU NCP Portal"},
    )


class EnhancedRegisterView(CreateView):
    """Class-based view for registration with enhanced features"""

    form_class = EnhancedUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()

        # Auto-login after successful registration
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
        )

        if user:
            login(self.request, user)
            messages.success(
                self.request,
                f"Welcome to EU NCP Portal, {user.first_name}! Your account has been created successfully.",
            )
            # Redirect to next page or home
            next_page = self.request.GET.get("next", "/")
            return redirect(next_page)

        return response

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below and try again.")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """Custom login view with HSE theming"""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        """Redirect to next page or home after successful login"""
        next_page = self.request.GET.get("next")
        if next_page:
            return next_page
        return "/"

    def form_valid(self, form):
        """Add success message on login"""
        messages.success(
            self.request,
            f"Welcome back, {form.get_user().first_name or form.get_user().username}!",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Add error message on failed login"""
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view"""

    template_name = "jinja2/registration/logout.html"

    def dispatch(self, request, *args, **kwargs):
        """Add logout message"""
        if request.user.is_authenticated:
            messages.success(request, "You have been successfully logged out.")
        return super().dispatch(request, *args, **kwargs)

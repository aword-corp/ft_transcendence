from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .admin import UserCreationForm, CustomAuthenticationForm
from db.models import User
from django.http import HttpResponseNotAllowed


def register_view(request):
    if request.user.is_authenticated and request.method in ["GET", "POST"]:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.cleaned_data.pop("password_confirmation")
            user = User.objects.create_user(**form.cleaned_data)
            if user is not None:
                login(request, user)
                return redirect("home")
        form.add_error(None, "Could not register")
        return render(request, "auth/register.html", {"form": form})
    elif request.method == "GET":
        form = UserCreationForm()
        return render(request, "auth/register.html", {"form": form})
    return HttpResponseNotAllowed(["GET", "POST"])


def login_view(request):
    if request.user.is_authenticated and request.method in ["GET", "POST"]:
        return redirect("home")
    if request.method == "POST":
        form = CustomAuthenticationForm(request.POST)
        if form.is_valid():
            user = User.get_user(
                form.cleaned_data.get("username"), form.cleaned_data.get("password")
            )
            if user is not None:
                login(request, user)
                return redirect("home")
        form.add_error(None, "Could not login")
        return render(request, "auth/login.html", {"form": form})
    elif request.method == "GET":
        form = CustomAuthenticationForm()
        return render(request, "auth/login.html", {"form": form})
    return HttpResponseNotAllowed(["GET", "POST"])


def logout_view(request):
    if not request.user.is_authenticated:
        return redirect("home")
    logout(request)
    return redirect("home")

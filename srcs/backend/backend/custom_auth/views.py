from django.shortcuts import render, redirect
from django.contrib.auth import login
from .admin import UserCreationForm
from db.models import User
from django.http import HttpResponseNotAllowed


def register_view(request):
    if request.user.is_authenticated and request.method in ["GET", "POST"]:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                username=form.cleaned_data["username"],
                region=form.cleaned_data["region"],
                country_code=form.cleaned_data["country_code"],
                language=form.cleaned_data["language"],
                birth_date=form.cleaned_data["birth_date"],
            )
            if user is not None:
                login(request, user)
                return redirect("home")
        form.add_error(None, "Could not register")
        return render(request, "auth/register.html", {"form": form})
    elif request.method == "GET":
        form = UserCreationForm()
        return render(request, "auth/register.html", {"form": form})
    return HttpResponseNotAllowed(["GET", "POST"])

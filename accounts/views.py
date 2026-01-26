from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import SignupForm
from users.models import Profile
from django.db import transaction

def signup(request):
    if request.user.is_authenticated:
        return redirect("case_list")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                # user.email = form.cleaned_data["email"].strip().lower()
                email = (form.cleaned_data.get("email") or "").strip().lower()
                user.email = email  # puede ser ""
                user.save()

                profile, _ = Profile.objects.get_or_create(user=user)
                profile.hospital_default = form.cleaned_data["hospital_default"].strip()
                profile.save()

            login(request, user)
            
            messages.success(request, "Cuenta creada. Bienvenido/a 👋")
            return redirect("case_list")

    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})

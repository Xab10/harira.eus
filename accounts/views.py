from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import SignupForm

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cuenta creada.")
            return redirect("case_list")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})

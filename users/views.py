from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count

from .models import Profile
from .forms import ProfileForm, GroupCreateForm

@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    pform = ProfileForm(instance=profile)
    gform = GroupCreateForm()

    if request.method == "POST":
        if "save_profile" in request.POST:
            pform = ProfileForm(request.POST, instance=profile)
            if pform.is_valid():
                pform.save()
                messages.success(request, "Perfil actualizado.")
                return redirect("profile")

        if "create_group" in request.POST:
            gform = GroupCreateForm(request.POST)
            if gform.is_valid():
                name = gform.cleaned_data["name"].strip()
                group, created = Group.objects.get_or_create(name=name)
                group.user_set.add(request.user)
                messages.success(request, f"Grupo '{name}' creado/añadido.")
                return redirect("profile")

    my_group_ids = request.user.groups.values_list("id", flat=True)

    my_groups = (
        Group.objects
        .filter(id__in=my_group_ids)
        .annotate(
            members_total=Count("user", distinct=True),
            cases_total=Count("shared_cases", distinct=True),
        )
        .prefetch_related("user_set")
        .order_by("name")
    )

    return render(request, "users/profile.html", {
        "pform": pform,
        "gform": gform,
        "my_groups": my_groups,
    })

@login_required
def group_leave(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    group.user_set.remove(request.user)
    messages.info(request, f"Has salido del grupo '{group.name}'.")
    return redirect("profile")
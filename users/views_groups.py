from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from cases.models import Case
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages

@login_required
def group_list(request):
    groups = (
        request.user.groups
        .annotate(member_count=Count("user"))
        .annotate(case_count=Count("shared_cases", distinct=True))  # related_name="cases"
        .order_by("name")
    )
    return render(request, "users/group_list.html", {"groups": groups})

@login_required
def group_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Solo miembros del grupo pueden invitar
    if not request.user.groups.filter(id=group.id).exists():
        messages.error(request, "No tienes permiso para invitar a este grupo.")
        return redirect("profile")

    username = (request.POST.get("username") or "").strip()
    if not username:
        messages.error(request, "Introduce un usuario.")
        return redirect("profile")

    user = User.objects.filter(username=username).first()
    if not user:
        messages.error(request, "Ese usuario no existe.")
        return redirect("profile")

    user.groups.add(group)
    messages.success(request, f"{user.username} añadido a {group.name}.")
    return redirect("profile")

@login_required
def group_create(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            g, created = Group.objects.get_or_create(name=name)
            g.user_set.add(request.user)  # el creador entra al grupo
            return redirect("group_detail", pk=g.id)
    return render(request, "users/group_create.html")

@login_required
def group_detail(request, pk):
    g = get_object_or_404(Group, pk=pk)

    # solo miembros (o staff)
    if not request.user.is_staff and not g.user_set.filter(id=request.user.id).exists():
        return redirect("group_list")

    cases = Case.objects.filter(shared_groups=g).distinct()

    return render(request, "users/group_detail.html", {
        "group": g,
        "member_count": g.user_set.count(),
        "case_count": cases.count(),
        "cases": cases,
        "members": g.user_set.order_by("username")
    })

@login_required
def group_members(request, pk):
    g = get_object_or_404(Group, pk=pk)

    # MVP: que solo staff gestione miembros (si quieres, luego lo abrimos a “creador”)
    if not request.user.is_staff:
        return redirect("group_detail", pk=g.id)

    if request.method == "POST":
        usernames = request.POST.get("usernames", "")
        for u in [x.strip() for x in usernames.splitlines() if x.strip()]:
            user = User.objects.filter(username=u).first()
            if user:
                g.user_set.add(user)
        return redirect("group_detail", pk=g.id)

    return render(request, "users/group_members.html", {"group": g})

@login_required
@require_POST
def group_create_ajax(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Nombre vacío"}, status=400)

    # Normaliza un poco
    name = " ".join(name.split())

    group, created = Group.objects.get_or_create(name=name)

    # Asegura que el usuario queda dentro del grupo al crearlo desde aquí
    request.user.groups.add(group)

    return JsonResponse({
        "id": group.id,
        "name": group.name,
        "created": created,
    })

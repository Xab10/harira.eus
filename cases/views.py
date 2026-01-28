from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Case, Tag
from .forms import CaseForm, CaseMediaFormSet, CaseMediaForm
from django.urls import reverse
from django.forms import inlineformset_factory

def user_can_access_case(user, case) -> bool:
    if case.created_by_id == user.id:
        return True
    return case.shared_groups.filter(
        id__in=user.groups.values_list("id", flat=True)
    ).exists()


@login_required
def cic_exists(request):
    cic = (request.GET.get("cic") or "").strip()
    pk = request.GET.get("pk")  # para excluir el caso actual en edición

    if not cic:
        return JsonResponse({"exists": False})

    # 🔒 Importante: solo casos "visibles" para este usuario
    qs = Case.objects.filter(
        Q(created_by=request.user) |
        Q(shared_groups__in=request.user.groups.all())
    ).distinct()

    # Busca por CIC
    qs = qs.filter(cic__iexact=cic)

    # Si estamos editando, excluye el propio caso
    if pk and pk.isdigit():
        qs = qs.exclude(pk=int(pk))

    case = qs.order_by("-id").first()  # si hubiese varios, coge el más reciente
    if not case:
        return JsonResponse({"exists": False})

    return JsonResponse({
        "exists": True,
        "case_id": case.pk,
        "edit_url": reverse("case_edit", args=[case.pk]),
    })

@login_required
def case_list(request):
    selected = {
        "seccion": request.GET.getlist("seccion"),
        "localizacion": request.GET.getlist("localizacion"),
        "patologia": request.GET.getlist("patologia"),
        "groups": request.GET.getlist("groups"),
        "docente": request.GET.get("docente"),
        "edad": request.GET.get("edad") or "",
    }

    edad = request.GET.get("edad") or "adulta"
    selected["edad"] = edad

    user_groups = request.user.groups.all()

    # Base queryset por permisos
    qs = Case.objects.filter(
            Q(created_by=request.user) |
            Q(shared_groups__in=request.user.groups.all())
        ).distinct()

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(cic=q) |
            Q(centro_medico__icontains=q) |
            Q(diagnostico_inicial__icontains=q) |
            Q(comentarios__icontains=q)
        )

    secciones_ids = request.GET.getlist("seccion")
    if secciones_ids:
        qs = qs.filter(secciones__id__in=secciones_ids)

    localizaciones_ids = request.GET.getlist("localizacion")
    if localizaciones_ids:
        qs = qs.filter(localizaciones__id__in=localizaciones_ids)

    patologias_ids = request.GET.getlist("patologia")
    if patologias_ids:
        qs = qs.filter(patologias__id__in=patologias_ids)

    group_ids = request.GET.getlist("groups")
    if group_ids:
        qs = qs.filter(shared_groups__id__in=group_ids)

    docente = request.GET.get("docente")
    if docente in ("1", "true", "True", "on"):
        qs = qs.filter(interes_docente=True)

    qs = qs.distinct().order_by("-fecha", "-id")

    edad = request.GET.get("edad")
    selected["edad"] = edad

    # Ajusta estos valores a los que tengas realmente guardados en Case.grupo_edad:
    if edad == "adulta":
        qs = qs.filter(grupo_edad__in=["adulta", "Adulta"])
    elif edad == "pediatrica":
        qs = qs.filter(grupo_edad__in=["pediatrica", "Pediatrica", "Pediátrica"])

    ctx = {
        "cases": qs,
        "q": q,
        "secciones": Tag.objects.filter(kind=Tag.Kind.SECCION),
        "localizaciones": Tag.objects.filter(kind=Tag.Kind.LOCALIZACION),
        "patologias": Tag.objects.filter(kind=Tag.Kind.PATOLOGIA),
        "my_groups": request.user.groups.all().order_by("name"),
        "selected": {
            "seccion": request.GET.getlist("seccion"),
            "localizacion": request.GET.getlist("localizacion"),
            "patologia": request.GET.getlist("patologia"),
            "groups": group_ids,
            "docente": docente,
            "edad": edad,
        }
    }
    return render(request, "cases/case_list.html", ctx)


@login_required
def case_create(request):
    if request.method == "POST":
        form = CaseForm(request.POST, user=request.user)
        media_formset = CaseMediaFormSet(request.POST, request.FILES)  # <-- crea aquí

        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            form.save_m2m()

            # Importantísimo: enlazar el formset al case ya guardado
            media_formset = CaseMediaFormSet(request.POST, request.FILES, instance=case)
            if media_formset.is_valid():
                media_formset.save()
            else:
                # Si no es válido, NO rompas el flujo: re-render con errores
                return render(request, "cases/case_form.html", {
                    "form": form,
                    "media_formset": media_formset,
                    "mode": "new",
                })

            # shared_groups (SIEMPRE, independientemente de multimedia)
            groups = form.cleaned_data.get("shared_groups", [])
            case.shared_groups.set(groups)
            request.user.groups.add(*groups)

            return redirect("case_list")

        # si el form NO es válido, renderiza con el formset (como lo tenías)
        media_formset = CaseMediaFormSet(request.POST, request.FILES)

    else:
        form = CaseForm(user=request.user)
        media_formset = CaseMediaFormSet()

    return render(request, "cases/case_form.html", {
        "form": form,
        "media_formset": media_formset,
        "mode": "new",
    })


@login_required
def case_edit(request, pk):
    case = get_object_or_404(Case, pk=pk)

    if not user_can_access_case(request.user, case):
        return redirect("case_list")

    if request.method == "POST":
        form = CaseForm(request.POST, instance=case, user=request.user)
        media_formset = CaseMediaFormSet(request.POST, request.FILES, instance=case)

        if form.is_valid() and media_formset.is_valid():
            case = form.save()  # no hace falta commit=False aquí

            # Guardar multimedia (esto faltaba)
            media_formset.save()

            # shared_groups
            case.shared_groups.set(form.cleaned_data.get("shared_groups", []))
            request.user.groups.add(*case.shared_groups.all())

            return redirect("case_list")

    else:
        form = CaseForm(instance=case, user=request.user)
        media_formset = CaseMediaFormSet(instance=case)

    return render(request, "cases/case_form.html", {
        "form": form,
        "media_formset": media_formset,
        "mode": "edit",
    })

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

@login_required
def case_delete(request, pk):
    case = get_object_or_404(Case, pk=pk)

    # Permisos MVP (igual que en case_list):
    if not user_can_access_case(request.user, case):
            return redirect("case_list")

    if request.method == "POST":
        case.delete()
        return redirect("case_list")

    return render(request, "cases/case_confirm_delete.html", {"case": case})

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from .models import Case, Tag, CaseMedia
from .forms import CaseForm, CaseMediaFormSet, CaseMediaForm
from django.urls import reverse
from django.forms import inlineformset_factory
from django.conf import settings
from google.cloud import storage

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
def private_media(request, path):
    """
    Sirve archivos privados desde GCS (o local en dev), controlando permisos por Case.
    path = "case_media/xxx.jpg"
    """
    # Busca el CaseMedia por el nombre exacto guardado en FileField
    media = get_object_or_404(CaseMedia, file=path)

    # Permisos: mismo criterio que usas para casos
    if not user_can_access_case(request.user, media.case):
        raise Http404()

    # DEV: si estás en local y usas MEDIA_ROOT
    if settings.DEBUG and getattr(settings, "DEFAULT_FILE_STORAGE", "") == "":
        # intenta servir desde disco
        import os
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        try:
            return FileResponse(open(full_path, "rb"))
        except FileNotFoundError:
            raise Http404()

    # PROD: Google Cloud Storage
    bucket_name = settings.GS_BUCKET_NAME  # ponlo en settings
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(path)

    if not blob.exists():
        raise Http404()

    # stream directo
    return FileResponse(blob.open("rb"), content_type=blob.content_type)

@login_required
def case_list(request):
    selected = {
        "seccion": request.GET.getlist("seccion"),
        "localizacion": request.GET.getlist("localizacion"),
        "patologia": request.GET.getlist("patologia"),
        "groups": request.GET.getlist("groups"),
        "docente": request.GET.get("docente"),
        "multimedia": request.GET.get("multimedia"),
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

    multimedia = request.GET.get("multimedia")
    if multimedia in ("1", "true", "True", "on"):
        qs = qs.filter(media__file__isnull=False).distinct()

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
            "multimedia": multimedia,
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


@login_required
def case_detail(request, pk):
    case = get_object_or_404(Case, pk=pk)

    if not user_can_access_case(request.user, case):
        return redirect("case_list")

    from .forms import PROC_CHOICES, PROC_GROUPS
    proc_labels = dict(PROC_CHOICES)

    procedimientos_with_labels = []
    for proc in case.procedimientos:
        label = proc_labels.get(proc, proc)
        procedimientos_with_labels.append((proc, label))

    ctx = {
        "case": case,
        "proc_groups": PROC_GROUPS,
        "proc_labels": proc_labels,
        "procedimientos_with_labels": procedimientos_with_labels,
    }
    return render(request, "cases/case_detail.html", ctx)

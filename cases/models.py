from django.conf import settings
from django.db import models
from django.contrib.auth.models import Group
import os
from django.utils.text import slugify

class Tag(models.Model):
    class Kind(models.TextChoices):
        SECCION = "seccion", "Sección"
        LOCALIZACION = "localizacion", "Localización"
        PATOLOGIA = "patologia", "Patología"
        SEMIOLOGIA = "semiologia", "Semiología"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=30, choices=Kind.choices)

    class Meta:
        unique_together = ("name", "kind")
        ordering = ["kind", "name"]

    def __str__(self):
        return self.name


class Case(models.Model):
    class AgeGroup(models.TextChoices):
        ADULTA = "adulta", "Adulta"
        PEDIATRICA = "pediatrica", "Pediátrica"

    cic = models.CharField(max_length=50, blank=True)
    centro_medico = models.CharField(max_length=150, blank=True)
    fecha = models.DateField(null=True, blank=True)

    grupo_edad = models.CharField(max_length=20, choices=AgeGroup.choices, default=AgeGroup.ADULTA)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="cases_created",
    )
    
    secciones = models.ManyToManyField(
        Tag, related_name="cases_seccion", blank=True,
        limit_choices_to={"kind": Tag.Kind.SECCION}
    )
    localizaciones = models.ManyToManyField(
        Tag, related_name="cases_localizacion", blank=True,
        limit_choices_to={"kind": Tag.Kind.LOCALIZACION}
    )
    patologias = models.ManyToManyField(
        Tag, related_name="cases_patologia", blank=True,
        limit_choices_to={"kind": Tag.Kind.PATOLOGIA}
    )

    diagnostico_inicial = models.TextField(blank=True)
    comentarios = models.TextField(blank=True)

    publicado = models.BooleanField(default=False)
    publicado_en = models.CharField(max_length=200, blank=True)

    # Checklists (MVP): listas guardadas como JSON
    pruebas_imagen = models.JSONField(default=list, blank=True)     # p.ej. ["TC", "RM"]
    procedimientos = models.JSONField(default=list, blank=True)

    interes_docente = models.BooleanField(default=False)

    # Compartir con grupos de Django
    shared_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="cases",   # IMPORTANTE para contar casos fácil
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="cases_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-created_at"]

    def __str__(self):
        return f"cic {self.cic} - {self.fecha or ''}"

    shared_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="shared_cases",
    )

def case_media_path(instance, filename):
    """
    Guarda como: case_media/<case_id>/<titulo-o-nombre-original>.<ext>
    """
    base, ext = os.path.splitext(filename)

    # Usa title si existe; si no, usa el nombre original del fichero
    name = instance.title.strip() if getattr(instance, "title", "") else base
    safe = slugify(name) or "archivo"

    # Si aún no existe case_id (muy raro en inlineformset, pero por seguridad):
    case_id = instance.case_id or "tmp"

    return f"case_media/{case_id}/{safe}{ext.lower()}"

class CaseMedia(models.Model):
    case = models.ForeignKey("Case", on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to=case_media_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    title = models.CharField("Nombre", max_length=120, blank=True)
    caption = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Media #{self.pk} (case {self.case_id})"

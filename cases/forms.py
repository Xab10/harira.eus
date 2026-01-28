from django import forms
from django.contrib.auth.models import Group
from .models import Case, CaseMedia
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .widgets import PrettyFileInput

IMAGING_CHOICES = [
    ("Ecografia", "Ecografía"),
    ("PET-TC", "PET-TC"),
    ("RM", "RM"),
    ("TC", "TC"),
    ("Rx", "Rx"),
]

PROC_CHOICES = [
    # Endourología / Litiasis / Obstrucción alta
    ("cistoscopia_diag", "Cistoscopia diagnóstica"),
    ("ursrirs_laser", "URS/RIRS + láser"),
    ("pcnl", "Nefrolitotomía percutánea (PCNL)"),
    ("mini_pcnl", "Mini-PCNL"),
    ("leoc", "Litotricia extracorpórea (LEOC/ESWL)"),
    ("doble_j", "Colocación/recambio catéter doble J"),
    ("nefrostomia", "Nefrostomía percutánea (colocación/recambio)"),
    ("dilatacion_ureteral", "Dilatación ureteral / endoureterotomía"),
    ("endopielotomia", "Endopielotomía / pieloplastia endoscópica"),

    # HBP y vejiga
    ("turbt", "RTU vesical (TURBT)"),
    ("biopsia_vesical", "Biopsia vesical endoscópica"),
    ("turp", "RTU próstata (TURP)"),
    ("holep", "HoLEP"),

    # Uretra / funcional
    ("dilatacion_uretral", "Dilatación uretral"),
    ("dviu", "Uretrotomía interna (DVIU)"),
    ("uretroplastia", "Uretroplastia"),
    ("cistostomia_suprapubica", "Cistostomía suprapúbica (catéter suprapúbico)"),

    # Próstata (diagnóstico)
    ("biopsia_trus", "Biopsia prostática transrectal"),
    ("biopsia_transperineal", "Biopsia prostática transperineal"),
    ("fusion_rm_ecografia", "Biopsia por fusión"),

    # Oncología renal/suprarrenal
    ("nefrectomia_parcial_robot", "Nefrectomía parcial robótica"),
    ("nefrectomia_parcial_lap", "Nefrectomía parcial laparoscópica"),
    ("nefrectomia_radical_robot", "Nefrectomía radical robótica"),
    ("nefrectomia_radical_lap", "Nefrectomía radical laparoscópica"),
    ("ablacion_renal", "Ablación tumoral renal (crio/RFA/microondas)"),

    # Oncología vesical
    ("cistectomia_robot", "Cistectomía radical robótica"),
    ("cutaneas", "Cistectomía con cutáneas"),
    ("bricker", "Derivación urinaria tipo Bricker"),
    ("neovejiga", "Neovejiga ortotópica"),

    # Oncología próstata
    ("prostatectomia_robot", "Prostatectomía radical robótica"),
    

    # Andrología / escroto
    ("vasectomia", "Vasectomía"),
    ("varicocelectomia", "Varicocelectomía"),
    ("circuncision", "Circuncisión"),
    ("hidrocelectomia", "Hidrocelectomía"),
    ("orquidopexia", "Orquidopexia / exploración escrotal (torsión)"),
    ("orquiectomia", "Orquiectomía"),
    ("protesis_pene", "Prótesis de pene"),
]

PROC_GROUPS = {
    "Endourología / Litiasis": {
        "cistoscopia_diag",
        "ursrirs_laser",
        "rirs_laser",
        "pcnl",
        "mini_pcnl",
        "leoc",
        "doble_j",
        "nefrostomia",
        "dilatacion_ureteral",
        "endopielotomia",
    },

    "Uretra / funcional": {
        "dilatacion_uretral",
        "dviu",
        "uretroplastia",
        "cistostomia_suprapubica",
    },

    "Oncología renal / suprarrenal": {
        "nefrectomia_parcial_robot",
        "nefrectomia_parcial_lap",
        "nefrectomia_radical_robot",
        "nefrectomia_radical_lap",
        "ablacion_renal",
    },
    "Oncología vesical": {
        "cistectomia_robot",
        "bricker",
        "neovejiga",
        "cutaneas",
        "turbt",
        "biopsia_vesical",
    },
    "Próstata": {
        "biopsia_trus",
        "biopsia_transperineal",
        "fusion_rm_ecografia",
        "prostatectomia_robot",
        "turp",
        "holep",
    },
    "Andrología / escroto": {
        "vasectomia",
        "varicocelectomia",
        "circuncision",
        "hidrocelectomia",
        "orquidopexia",
        "orquiectomia",
        "protesis_pene",
    },
}

class LooseMultipleChoiceField(forms.MultipleChoiceField):
    # deja pasar valores que no estén en choices (para permitir crear)
    def validate(self, value):
        return


class CaseForm(forms.ModelForm):
    pruebas_imagen = forms.MultipleChoiceField(choices=IMAGING_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)
    procedimientos = forms.MultipleChoiceField(choices=PROC_CHOICES, required=False, widget=forms.CheckboxSelectMultiple)
    shared_groups = LooseMultipleChoiceField(
        required=False,
        choices=(),
        widget=forms.SelectMultiple(attrs={
            "class": "ts-select",
            "data-create": "1",
            "placeholder": "Para crear un nuevo grupo escríbelo y pulsa Enter",
        })
    )
    
    def clean_shared_groups(self):
        raw = self.data.getlist(self.add_prefix("shared_groups"))

        # Construimos un “índice” de choices permitidos (ids de grupos del usuario)
        allowed_ids = {str(value) for value, _label in (self.fields["shared_groups"].choices or [])}

        resolved = []
        seen_ids = set()

        for v in raw:
            v = (v or "").strip()
            if not v:
                continue

            # Si viene como id existente (de los choices)
            if v in allowed_ids and v.isdigit():
                g = Group.objects.filter(pk=int(v)).first()
                if g and g.pk not in seen_ids:
                    resolved.append(g)
                    seen_ids.add(g.pk)
                continue

            # Si viene como texto -> crear/buscar
            g, _ = Group.objects.get_or_create(name=v)
            if g.pk not in seen_ids:
                resolved.append(g)
                seen_ids.add(g.pk)

        return resolved

    def clean(self):
        cleaned = super().clean()
        publicado = cleaned.get("publicado")
        publicado_en = cleaned.get("publicado_en", "").strip()

        if publicado and not publicado_en:
            self.add_error("publicado_en", "Indica dónde se ha publicado.")
        return cleaned 
    
    def clean_cic(self):
        cic = (self.cleaned_data.get("cic") or "").strip()
        if not cic:
            return cic

        qs = Case.objects.filter(cic__iexact=cic)

        # Si estamos editando, excluye el propio caso
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("Ya existe un caso con este CIC. Revisa la lista antes de crear uno nuevo.")

        return cic

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Etiqueta visible
        self.fields["cic"].label = "CIC"

        # Para la UI de procedimientos agrupados
        self.proc_groups = PROC_GROUPS
        self.proc_labels = dict(PROC_CHOICES)
        self.selected_procedimientos = set(self["procedimientos"].value() or [])

        # ✅ Defaults SOLO al crear (no al editar)
        if not getattr(self.instance, "pk", None):

            # fecha por defecto (si no viene en POST)
            if not self.data.get("fecha") and not self.initial.get("fecha"):
                self.initial["fecha"] = timezone.localdate()

            # hospital por defecto (si no viene en POST)
            if user is not None and not self.initial.get("centro_medico"):
                hosp = getattr(getattr(user, "profile", None), "hospital_default", "")
                if hosp:
                    self.initial["centro_medico"] = hosp

        if user is not None:
            user_qs = user.groups.all()
        else:
            user_qs = Group.objects.none()

        instance_qs = self.instance.shared_groups.all() if getattr(self.instance, "pk", None) else Group.objects.none()

        # Opciones = grupos del usuario + los ya asociados al caso (para no “perderlos”)
        qs = (user_qs | instance_qs).distinct().order_by("name")
        self.fields["shared_groups"].choices = [(str(g.pk), g.name) for g in qs]

        # Al editar (GET), marcar los grupos actuales como seleccionados
        if getattr(self.instance, "pk", None) and not self.is_bound:
            self.initial["shared_groups"] = [str(g.pk) for g in instance_qs]

        self.fields["cic"].label = "CIC"
        self.fields["shared_groups"].widget.attrs.update({
            "class": "ts-select",
            "placeholder": "Para crear un nuevo grupo escríbelo y pulsa Enter",
        })

    class Meta:
        model = Case
        fields = [
            "cic", "centro_medico", "fecha",
            "grupo_edad",
            "secciones", "localizaciones", "patologias",
            "diagnostico_inicial", "comentarios",
            "pruebas_imagen", "procedimientos", "publicado", "publicado_en", "interes_docente",
            "shared_groups",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "diagnostico_inicial": forms.Textarea(attrs={"rows": 2}),
            "comentarios": forms.Textarea(attrs={"rows": 2}),
            "secciones": forms.SelectMultiple(attrs={"class": "form-select tomselect", "placeholder": "Escribe para buscar..."}),
            "localizaciones": forms.SelectMultiple(attrs={"class": "form-select tomselect", "placeholder": "Escribe para buscar..."}),
            "patologias": forms.SelectMultiple(attrs={"class": "form-select tomselect", "placeholder": "Escribe para buscar..."}),
            "publicado_en": forms.TextInput(attrs={"placeholder": "Tipo de publicación, lugar y fecha"}),
        }

class CaseMediaForm(forms.ModelForm):
    class Meta:
        model = CaseMedia
        fields = ["caption", "url", "file"]
        widgets = {
            "caption": forms.TextInput(attrs={"class": "form-control", "placeholder": "Descripción (opcional)"}),
            "file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*,video/*",
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: TAC preoperatorio"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            }),
        }

CaseMediaFormSet = inlineformset_factory(
    Case,
    CaseMedia,
    form=CaseMediaForm,
    extra=1,          # empieza con 1 fila vacía
    can_delete=True,  # permite eliminar archivos existentes
)
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=False, # True para hacerlo obligatorio
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    hospital_default = forms.CharField(
        required=False,
        label="Hospital de referencia",
        widget=forms.TextInput()
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        # email = self.cleaned_data["email"].strip().lower()
        email = (self.cleaned_data.get("email") or "").strip().lower()

        # return email
        if not email:
            return ""

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese email.")

    def save(self, commit=True):
        user = super().save(commit=False)

        # obtener valores de forma segura (evita None.strip())
        email = (self.cleaned_data.get("email") or "").strip().lower()
        first_name = (self.cleaned_data.get("first_name") or "").strip()
        last_name = (self.cleaned_data.get("last_name") or "").strip()
        hospital = (self.cleaned_data.get("hospital") or "").strip()  # <- ejemplo

        # asignaciones al modelo
        user.email = email or user.email
        user.first_name = first_name
        user.last_name = last_name

        # cualquier campo extra en tu modelo
        if hasattr(user, "hospital"):
            user.hospital = hospital

        if commit:
            user.save()
            # si tienes ManyToMany u otras relaciones: form.save_m2m()
        return user

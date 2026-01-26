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
        user.email = self.cleaned_data["email"].strip().lower()
        if commit:
            user.save()
        return user

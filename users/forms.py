from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    hospital_default = forms.CharField(
        label="",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = Profile
        fields = ["hospital_default"]

class GroupCreateForm(forms.Form):
    name = forms.CharField(
        label="Nuevo grupo",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del grupo"})
    )

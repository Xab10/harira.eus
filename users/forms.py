from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["hospital_default"]   # o el nombre que uses

class GroupCreateForm(forms.Form):
    name = forms.CharField(
        label="Nuevo grupo",
        max_length=80,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del grupo"})
    )

from django.contrib.auth.forms import UserCreationForm

class CleanUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ("username", "password1", "password2"):
            self.fields[f].help_text = ""

from django.forms.widgets import ClearableFileInput
from django.utils.safestring import mark_safe

class PrettyFileInput(ClearableFileInput):
    """
    Renderiza SOLO el input file (sin 'Currently' ni checkbox Clear).
    """
    template_name = "widgets/pretty_file_input.html"

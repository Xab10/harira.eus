from django.core.management.base import BaseCommand
from cases.models import Tag


SECCIONES = [
    # Ajusta esta lista a vuestro servicio
    "Urología",
    "Oncología",
    "Endourología / Litiasis",
    "Urología funcional",
    "Andrología",
    "Urología pediátrica",
    "Reconstrucción / Uretroplastia",
    "Trasplante",
    "Urgencias urológicas",
    "Intervencionismo",
    "Consultas externas",
    "Planta",
    "Quirófano",
]


class Command(BaseCommand):
    help = "Crea tags iniciales de Sección"

    def handle(self, *args, **options):
        created = 0
        for name in SECCIONES:
            _, was_created = Tag.objects.get_or_create(
                name=name,
                kind=Tag.Kind.SECCION
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f"OK. Secciones creadas nuevas: {created}"))

from django.core.management.base import BaseCommand
from cases.models import Tag


LOCALIZACIONES = [
    "Riñón", "Pelvis renal", "Cálices", "Unión pieloureteral (UPU)",
    "Uréter proximal", "Uréter medio", "Uréter distal",
    "Vejiga", "Trígono vesical", "Cuello vesical",
    "Uretra", "Uretra prostática", "Uretra bulbar", "Uretra peneana", "Meato uretral",
    "Próstata", "Vesículas seminales",
    "Testículo", "Epidídimo", "Cordón espermático", "Escroto", "Pene",
    "Glándula suprarrenal", "Retroperitoneo",
]

PATOLOGIAS = [
    "ITU (infección urinaria)", "Pielonefritis", "Cistitis", "Prostatitis",
    "Epididimitis / orquiepididimitis", "Uretritis", "Absceso renal / perirrenal",
    "Litiasis renal", "Litiasis ureteral", "Litiasis vesical", "Obstrucción ureteral",
    "Hidronefrosis", "Estenosis UPU", "Estenosis ureteral", "Estenosis uretral",
    "Retención aguda de orina (RAO)", "Cólico renal",
    "Tumor renal", "Masa renal indeterminada", "Tumor urotelial (vía urinaria alta)",
    "Tumor vesical (urotelial)", "Cáncer de próstata", "Tumor testicular",
    "Tumor suprarrenal", "Metástasis / recidiva", "Adenopatías (pelvianas / retroperitoneales)",
    "HBP (Hiperplasia benigna de próstata)", "LUTS", "Incontinencia urinaria", "Vejiga neurógena / disfunción miccional",
    "Reflujo vesicoureteral",
    "Trauma renal", "Trauma ureteral", "Trauma vesical", "Trauma uretral",
    "Hematuria",
    "Duplicidad pieloureteral", "Riñón en herradura", "Ectopia renal",
    "Divertículo vesical", "Válvulas uretrales posteriores",
    "Fuga urinaria / urinoma", "Complicación quirúrgica",
]


class Command(BaseCommand):
    help = "Crea tags iniciales de Localización y Patología"

    def handle(self, *args, **options):
        created = 0

        for name in LOCALIZACIONES:
            _, was_created = Tag.objects.get_or_create(name=name, kind=Tag.Kind.LOCALIZACION)
            created += int(was_created)

        for name in PATOLOGIAS:
            _, was_created = Tag.objects.get_or_create(name=name, kind=Tag.Kind.PATOLOGIA)
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f"OK. Tags creados nuevos: {created}"))

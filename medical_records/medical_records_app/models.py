from django.db import models
from django.utils import timezone

class MedicalRecord(models.Model):
    patient = models.ForeignKey('auth_app.Patient', on_delete=models.CASCADE, null=True)
    doctor = models.ForeignKey('auth_app.Doctor', on_delete=models.CASCADE, null=True)
    description = models.TextField(null=True, blank=True)
    diagnostic = models.TextField(null=True, blank=True)
    treatment = models.TextField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dossier médical de {self.patient} par {self.doctor} le {self.created_at}"

    def formatted_created_at(self):
        return self.created_at.strftime("%d %B %Y à %H:%M")

    def formatted_updated_at(self):
        return self.updated_at.strftime("%d %B %Y à %H:%M")
    def save(self, *args, **kwargs):
        # Si ce n'est pas une nouvelle création (i.e., une mise à jour)
        if self.pk:
            # Récupérer le dernier numéro de version et incrémenter
            last_version = MedicalRecordArchive.objects.filter(original_record=self).count()
            
            # Créer une archive avant de sauvegarder le dossier médical
            MedicalRecordArchive.objects.create(
                original_record=self,
                doctor=self.doctor,
                patient=self.patient,
                description=self.description,
                diagnostic=self.diagnostic,
                treatment=self.treatment,
                follow_up_date=self.follow_up_date,
                created_at=self.created_at,
                version=last_version + 1  # Incrémenter la version
            )
        
        # Appeler la méthode `save` du parent pour sauvegarder le dossier médical
        super().save(*args, **kwargs)



class MedicalRecordArchive(models.Model):
    original_record = models.ForeignKey('MedicalRecord', on_delete=models.CASCADE, related_name='archives')
    doctor = models.ForeignKey('auth_app.Doctor', on_delete=models.CASCADE)
    patient = models.ForeignKey('auth_app.Patient', on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    diagnostic = models.TextField(null=True, blank=True)
    treatment = models.TextField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(default=timezone.now)

    version = models.PositiveIntegerField()  # Numéro de version de l'archive

    class Meta:
        ordering = ['-version']  # Tri par version décroissante

    def __str__(self):
        return f"Archive du dossier {self.original_record} - Version {self.version}"

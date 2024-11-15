from django import forms
from .models import MedicalRecord
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
import requests
from django.core.exceptions import ValidationError

class MedicalRecordForm(forms.ModelForm):
    # Fields for creating a new patient
    patient_nom = forms.CharField(label="Nom du patient", max_length=100, required=True)
    patient_prenom = forms.CharField(label="Prénom du patient", max_length=100, required=True)
    patient_email = forms.EmailField(label="Email du patient", required=True)
    patient_ramq = forms.CharField(label="Numéro RAMQ du patient", max_length=50, required=True)
    patient_password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe temporaire", required=True)
    patient_image = forms.ImageField(label="Image du patient", required=True)
    patient_voice_recording = forms.FileField(label="Voice du patient", required=True)
    patient_date_naissance = forms.DateField(label="Date de naissance", required=True, widget=forms.SelectDateWidget(years=range(1900, 2025)))
    patient_genre = forms.ChoiceField(label="Genre", choices=[('M', 'Masculin'), ('F', 'Féminin'), ('O', 'Autre')], required=True)
    patient_ville_naissance = forms.CharField(label="Ville de naissance", max_length=100, required=True)
    patient_adresse = forms.CharField(label="Adresse de la maison", max_length=255, required=True)
    patient_telephone = forms.CharField(label="Téléphone", max_length=20, required=True)

    class Meta:
        model = MedicalRecord
        fields = ['description', 'diagnostic', 'treatment', 'follow_up_date']

    def clean_patient_image(self):
        image = self.cleaned_data.get('patient_image')
        if image:
            if not image.content_type in ['image/jpeg', 'image/png', 'image/jpg']:
                raise ValidationError("Seuls les fichiers JPEG, JPG et PNG sont autorisés.")
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("La taille de l'image ne doit pas dépasser 5 Mo.")
        return image 

    def save(self, commit=True):
        return super().save(commit=commit)

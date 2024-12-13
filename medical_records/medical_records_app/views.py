from django.shortcuts import render, get_object_or_404, redirect
from .models import MedicalRecord, MedicalRecordArchive
from .forms import MedicalRecordForm
from django.contrib import messages
import requests
from django.db import transaction
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa 




def homepage(request):
    return render(request, 'homepage.html')

def doctor_profile(request):
    doctor_data = get_doctor_data(request)

    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    context = {
        'doctor_name': f"{doctor_data.get('nom')} {doctor_data.get('prenom')}",
        'doctor_email': doctor_data.get('email'),
        'doctor_licence': doctor_data.get('numero_licence'),
        'doctor_image': doctor_data.get('image'),  
        'doctor_subscription': doctor_data.get('subscription'), 
    }
    return render(request, 'doctor_profile.html', context)



def view_archives(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    archives = record.archives.all()  # Récupérer toutes les archives liées au dossier

    context = {
        'record': record,
        'archives': archives
    }
    return render(request, 'view_archives.html', context)
def view_archive_version(request, archive_id):
    archive = get_object_or_404(MedicalRecordArchive, id=archive_id)

    context = {
        'archive': archive
    }
    return render(request, 'view_archive_version.html', context)


def revert_to_version(request, archive_id):
    archive = get_object_or_404(MedicalRecordArchive, id=archive_id)
    record = archive.original_record

    # Remplacer les données du dossier par celles de l'archive
    record.description = archive.description
    record.diagnostic = archive.diagnostic
    record.treatment = archive.treatment
    record.follow_up_date = archive.follow_up_date

    # Sauvegarder le dossier médical mis à jour
    record.save()

    # Rediriger vers la page des archives ou un message de succès
    return redirect('view_archives', record_id=record.id)


def get_doctor_data(request):
    """
    Vérifie si le docteur est connecté et retourne ses données.
    Si le docteur n'est pas trouvé ou l'email est vide, redirige vers la page de connexion.
    """
    email = request.GET.get('email') or request.session.get('doctor_email')

    if email:
        api_url = f'http://127.0.0.1:8000/auth/api/doctor/{email}/'
        response = requests.get(api_url)

        if response.status_code == 200:
            request.session['doctor_email'] = email
            return response.json()
        else:
            return None
    return None

def doctor_medical_record_list(request):
    # Récupérer les données du docteur
    doctor_data = get_doctor_data(request)
    
    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    # Récupérer les dossiers médicaux pour le docteur
    doctor_id = doctor_data.get('id')
    records = MedicalRecord.objects.filter(doctor_id=doctor_id)

    context = {
        'records': records,
        'doctor_name': f"{doctor_data.get('nom')} {doctor_data.get('prenom')}",
        'doctor_email': doctor_data.get('email'),
        'doctor_image': doctor_data.get('image'),
        'doctor_licence': doctor_data.get('numero_licence'),
    }
    return render(request, 'doctor_record_list.html', context)


import requests

FASTAPI_FACE_URL = 'http://127.0.0.1:8021/add-signature/'  # URL de FastAPI pour ajouter une signature faciale
FASTAPI_VOICE_URL = 'http://127.0.0.1:8022/add-voice-signature/'  # URL de FastAPI pour ajouter une signature vocale

def create_medical_record(request):
    doctor_data = get_doctor_data(request)

    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    doctor_id = doctor_data.get('id')

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES)
        if form.is_valid():
            # Créer le dossier médical, mais ne pas encore le sauvegarder
            medical_record = form.save(commit=False)

            # Récupérer les informations du patient depuis le formulaire
            patient_email = form.cleaned_data.get('patient_email')
            patient_nom = form.cleaned_data.get('patient_nom')
            patient_prenom = form.cleaned_data.get('patient_prenom')
            patient_ramq = form.cleaned_data.get('patient_ramq')
            patient_password = form.cleaned_data.get('patient_password')
            patient_image = form.cleaned_data.get('patient_image')
            patient_voice_recording = form.cleaned_data.get('patient_voice_recording')  # Récupérer l'audio
            patient_date_naissance = form.cleaned_data.get('patient_date_naissance')
            patient_genre = form.cleaned_data.get('patient_genre')
            patient_ville_naissance = form.cleaned_data.get('patient_ville_naissance')
            patient_adresse = form.cleaned_data.get('patient_adresse')
            patient_telephone = form.cleaned_data.get('patient_telephone')

            # Créer un nouveau patient via l'API
            patient_data = {
                'email': patient_email,
                'nom': patient_nom,
                'prenom': patient_prenom,
                'ramq': patient_ramq,
                'password': patient_password,
                'date_naissance': patient_date_naissance,
                'genre': patient_genre,
                'ville_naissance': patient_ville_naissance,
                'adresse': patient_adresse,
                'telephone': patient_telephone,
            }

            # Inclure l'image et le fichier audio dans les fichiers à uploader
            files = {
                'image': (patient_image.name, patient_image, patient_image.content_type),
                'voice_recording': (patient_voice_recording.name, patient_voice_recording, patient_voice_recording.content_type)
            }

            # Envoyer les données du patient à l'API Django
            create_patient_response = requests.post(
                'http://localhost:8000/auth/api/patients/create',
                data=patient_data,
                files=files
            )

            if create_patient_response.status_code == 201:
                patient_id = create_patient_response.json().get('id')
                medical_record.patient_id = patient_id
                medical_record.doctor_id = doctor_id  # Associer au bon docteur
                
                # Sauvegarder le dossier médical
                medical_record.save()

                # Ajouter la signature faciale via FastAPI
                try:
                    with patient_image.open('rb') as image_file:
                        response = requests.post(
                            FASTAPI_FACE_URL,  # URL de FastAPI pour ajouter une signature faciale
                            files={'file': image_file},
                            data={'email': patient_email}
                        )
                    if response.status_code != 200:
                        raise Exception("Erreur lors de la création de la signature faciale.")
                except Exception as e:
                    messages.error(request, "Erreur lors de la création de la signature faciale.")
                    return redirect('doctor_medical_record_list')

                # Ajouter la signature vocale via FastAPI
                try:
                    if patient_voice_recording:
                        with patient_voice_recording.open('rb') as voice_file:
                            voice_response = requests.post(
                                FASTAPI_VOICE_URL,  # URL de FastAPI pour ajouter une signature vocale
                                files={'file': voice_file},
                                data={'email': patient_email}
                            )
                        if voice_response.status_code != 200:
                            raise Exception("Erreur lors de l'ajout de l'enregistrement vocal.")
                    else:
                        raise Exception("Enregistrement vocal manquant.")

                except Exception as e:
                    messages.error(request, f"Dossier créé, mais erreur lors de l'ajout de la signature vocale : {str(e)}")
                    return redirect('doctor_medical_record_list')

                # Succès si tout s'est bien passé
                messages.success(request, "Dossier médical, signature faciale, et vocale créés avec succès !")
                return redirect('doctor_medical_record_list')

            else:
                messages.error(request, "Erreur lors de la création du patient.")
                return redirect('create_medical_record')
    else:
        form = MedicalRecordForm()

    context = {
        'form': form,
    }

    return render(request, 'create_record.html', context)




def medical_record_detail(request, record_id):
    doctor_data = get_doctor_data(request)
    
    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')
    
    doctor_id = doctor_data.get('id')
    record = get_object_or_404(MedicalRecord, id=record_id, doctor_id=doctor_id)
    patient = record.patient
    
    context = {
        'record': record,
        'patient': patient,
        'doctor_name': f"{doctor_data.get('nom')} {doctor_data.get('prenom')}",
        'doctor_email': doctor_data.get('email'),
    }
    
    return render(request, 'record_detail.html', context)




def update_medical_record(request, record_id):
    doctor_data = get_doctor_data(request)

    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    doctor_id = doctor_data.get('id')

    # Récupérer le dossier médical pour ce docteur spécifique
    record = get_object_or_404(MedicalRecord, id=record_id, doctor_id=doctor_id)

    if request.method == 'POST':
        # Limiter les champs visibles
        form = MedicalRecordForm(request.POST, instance=record)
        form.fields = {field: form.fields[field] for field in ['description', 'diagnostic', 'treatment', 'follow_up_date']}

        if form.is_valid():
            form.save()
            messages.success(request, "Dossier médical mis à jour avec succès !")
            return redirect('medical_record_detail', record_id=record.id)

        else:
            messages.error(request, "Erreur lors de la mise à jour. Veuillez vérifier les informations fournies.")
    else:
        form = MedicalRecordForm(instance=record)
        form.fields = {field: form.fields[field] for field in ['description', 'diagnostic', 'treatment', 'follow_up_date']}

    context = {
        'form': form,
        'record': record,
        'doctor_email': doctor_data.get('email'),
    }

    return render(request, 'update_record.html', context)


def delete_medical_record(request, record_id):
    doctor_data = get_doctor_data(request)
    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    doctor_id = doctor_data.get('id')
    record = get_object_or_404(MedicalRecord, id=record_id, doctor_id=doctor_id)
    patient = record.patient  

    if request.method == 'POST':
        with transaction.atomic():
            record.delete()  
            patient.delete()  

        messages.success(request, "Dossier médical et compte du patient supprimés avec succès !")
        return redirect('doctor_medical_record_list')

    messages.error(request, "Action non autorisée.")
    return redirect('doctor_medical_record_list')



def get_medical_record(request, patient_id):
    try:
        record = MedicalRecord.objects.get(patient_id=patient_id)
        data = {
            'description': record.description,
            'diagnostic': record.diagnostic,
            'treatment': record.treatment,
            'created_at': record.created_at,
            'updated_at': record.updated_at,
            'doctor_nom': record.doctor.nom,
            'doctor_prenom': record.doctor.prenom,
        }
        return JsonResponse(data)
    except MedicalRecord.DoesNotExist:
        return JsonResponse({'error': 'No medical record found for this patient.'}, status=404)
    



PDF_MICROSERVICE_URL = "http://localhost:8002"

def pdf_chat_page(request):
    doctor_data = get_doctor_data(request)
    if not doctor_data or doctor_data.get('subscription') not in ['pro', 'enterprise']:
        messages.error(request, "Cette fonctionnalité est disponible uniquement pour les abonnements Pro et Enterprise.")
        return redirect('doctor_profile')

    return render(request, "pdf_chat.html")


# Endpoint pour télécharger un PDF et l'envoyer au microservice
@csrf_exempt
@require_POST
def upload_pdf(request):
    if request.method == "POST" and request.FILES.get("file"):
        try:
            file = request.FILES["file"]
            # Envoyer le fichier au microservice
            response = requests.post(
                f"{PDF_MICROSERVICE_URL}/upload/",
                files={"file": file},
            )
            if response.status_code == 200:
                return JsonResponse({"message": "PDF analysé avec succès"})
            return JsonResponse(
                {"message": response.json().get("message", "Erreur lors de l'analyse du PDF")},
                status=response.status_code,
            )
        except Exception as e:
            return JsonResponse({"message": f"Erreur de communication avec le microservice : {str(e)}"}, status=500)

    return JsonResponse({"message": "Aucun fichier fourni"}, status=400)

import json
# Endpoint pour poser une question au microservice
@csrf_exempt  
@require_POST
def ask_question(request):
    try:
        # Charger le contenu de la requête POST (JSON)
        data = json.loads(request.body)

        # Récupérer la question
        question = data.get("question", "").strip()

        if not question:
            return JsonResponse({"response": "Aucune question fournie"}, status=400)

        # Appeler le microservice pour poser la question
        response = requests.post(
            f"{PDF_MICROSERVICE_URL}/ask-question/",
            json={"question": question},
        )

        if response.status_code == 200:
            return JsonResponse(response.json())
        return JsonResponse(
            {"response": response.json().get("response", "Erreur lors de la recherche dans le PDF")},
            status=response.status_code,
        )
    except json.JSONDecodeError:
        return JsonResponse({"response": "Format de données invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"response": f"Erreur de communication avec le microservice : {str(e)}"}, status=500)




def download_medical_record_pdf(request, record_id):
    doctor_data = get_doctor_data(request)
    
    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')
    
    doctor_id = doctor_data.get('id')
    record = get_object_or_404(MedicalRecord, id=record_id, doctor_id=doctor_id)
    patient = record.patient

    # Charger le template HTML pour le PDF
    template_path = 'medical_record_pdf.html'
    context = {
        'record': record,
        'patient': patient,
        'doctor_name': f"{doctor_data.get('nom')} {doctor_data.get('prenom')}",
    }
    template = get_template(template_path)
    html = template.render(context)

    # Générer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dossier_medical_{patient.nom}_{patient.prenom}.pdf"'

    # Convertir le HTML en PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Une erreur est survenue lors de la génération du PDF.', status=500)

    return response


API_BASE_URL = "http://127.0.0.1:8000"  

def update_doctor_profile(request):
    doctor_data = get_doctor_data(request)

    if not doctor_data:
        messages.error(request, "Veuillez vous connecter.")
        return redirect('http://127.0.0.1:8000/auth/login/')

    doctor_id = doctor_data.get('id')  
    if not doctor_id:
        messages.error(request, "Impossible de récupérer l'ID du docteur.")
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        form_data = {
            'nom': request.POST.get('nom'),
            'prenom': request.POST.get('prenom'),
            'email': request.POST.get('email'),
            'numero_licence': request.POST.get('numero_licence'),
            'subscription': request.POST.get('subscription'),  # Ajout de l'abonnement
        }
        files = {
            'image': request.FILES.get('image'),
            'voice_recording': request.FILES.get('voice_recording'),
        }

        # Envoyer la requête PUT au microservice principal
        response = requests.put(
            f"{API_BASE_URL}/auth/api/doctors/{doctor_id}/update/",
            data=form_data,
            files=files,
        )

        if response.status_code == 200:
            messages.success(request, "Vos informations ont été mises à jour avec succès !")
            return redirect('doctor_profile')
        else:
            messages.error(request, "Erreur lors de la mise à jour. Veuillez réessayer.")

    context = {
        'doctor': doctor_data,
    }
    return render(request, 'update_doctor_profile.html', context)




def analyze_image_view(request):
    return render(request, "analyze_image.html")

import logging

logger = logging.getLogger(__name__)
OLLAMA_QUERY_URL = "http://127.0.0.1:8003/ollama_query/"

IMAGE_ANALYSIS_URL = "http://127.0.0.1:8003/predict/"


@csrf_exempt
@require_POST
def upload_image(request):
    """
    Télécharge une image depuis le client, l'envoie au microservice pour analyse,
    et retourne la classe prédite ainsi que la confiance ainsi qu'une explication détaillée.
    """
    if request.method == "POST" and request.FILES.get("file"):
        try:
            # Récupérer le fichier envoyé
            file = request.FILES["file"]
            
            # Envoyer le fichier au microservice d'analyse d'image
            response = requests.post(
                IMAGE_ANALYSIS_URL,
                files={"file": file},
            )

            # Vérifier si la requête a réussi
            if response.status_code == 200:
                result = response.json()
                anomaly = result.get("anomaly", "Non détecté")
                confidence = result.get("confidence", 0)

                # Construire les données pour interroger Ollama
                ollama_data = {
                    "class": anomaly,
                    "confidence": confidence,
                }

                # Envoyer les données à Ollama
                ollama_response = requests.post(
                    OLLAMA_QUERY_URL,
                    json=ollama_data,
                )

                if ollama_response.status_code == 200:
                    explanation = ollama_response.json().get("response", "Aucune explication fournie.")
                    return JsonResponse({
                        "message": "Image analysée avec succès",
                        "anomaly": anomaly,
                        "confidence": confidence,
                        "explanation": explanation,
                    })

                # Gérer les erreurs renvoyées par Ollama
                return JsonResponse(
                    {"message": "Erreur lors de l'interrogation d'Ollama."},
                    status=ollama_response.status_code,
                )

            # Gérer les erreurs renvoyées par le microservice d'analyse d'image
            return JsonResponse(
                {"message": response.json().get("error", "Erreur lors de l'analyse de l'image")},
                status=response.status_code,
            )

        except Exception as e:
            # Gérer les erreurs de communication avec le microservice
            return JsonResponse(
                {"message": f"Erreur de communication avec le microservice : {str(e)}"},
                status=500,
            )

    # Gérer le cas où aucun fichier n'est fourni
    return JsonResponse({"message": "Aucun fichier fourni"}, status=400)

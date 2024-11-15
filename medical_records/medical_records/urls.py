"""
URL configuration for medical_records project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LoginView
from medical_records_app.views import create_medical_record,doctor_medical_record_list, medical_record_detail, delete_medical_record, homepage, update_medical_record, get_medical_record, view_archives, revert_to_version, view_archive_version

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage, name='homepage'),
    path('login/', LoginView.as_view(), name='login'),
    path('records/',doctor_medical_record_list, name='doctor_medical_record_list'),
    path('records/create/', create_medical_record, name='create_medical_record'),
    path('records/<int:record_id>/', medical_record_detail, name='medical_record_detail'),
    path('records/<int:record_id>/update/', update_medical_record, name='update_medical_record'),
    path('records/<int:record_id>/delete/',delete_medical_record, name='delete_medical_record'),
    path('api/records/<int:patient_id>/', get_medical_record, name='get_medical_record'),
    path('records/<int:record_id>/archives/', view_archives, name='view_archives'),
    path('archives/<int:archive_id>/revert/', revert_to_version, name='revert_to_version'),
    path('archives/version/<int:archive_id>/', view_archive_version, name='view_archive_version'),
]

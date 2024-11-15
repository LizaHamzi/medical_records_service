from django.contrib import admin
from .models import MedicalRecord

class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'description', 'diagnostic', 'treatment', 'follow_up_date')

admin.site.register(MedicalRecord, MedicalRecordAdmin)

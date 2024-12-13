from medical_records_app.views import get_doctor_data  

def user_subscription(request):
    doctor_data = get_doctor_data(request)
    if doctor_data:
        return {'user_subscription': doctor_data.get('subscription')}
    return {'user_subscription': None}

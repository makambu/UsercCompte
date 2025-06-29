from django.utils import timezone
from django.conf import settings

class UpdateLastConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user_id = request.session.get('user_id')
        if user_id:
            try:
                from App_UserCompte.models import Profil  # adapte selon ton app
                profil = Profil.objects.get(id=user_id)
                profil.derniere_connexion = timezone.now()
                profil.save(update_fields=['derniere_connexion'])
            except Profil.DoesNotExist:
                pass

        return response

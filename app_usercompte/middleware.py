from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib import messages
from app_usercompte.models import Profil

class UpdateLastConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user_id = request.session.get('user_id')
        if user_id:
            try:
                from app_usercompte.models import Profil  # adapte selon ton app
                profil = Profil.objects.get(id=user_id)
                profil.derniere_connexion = timezone.now()
                profil.save(update_fields=['derniere_connexion'])
            except Profil.DoesNotExist:
                pass

        return response

class InvalidUserSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            if not Profil.objects.filter(id=user_id).exists():
                # Supprimer la session si le profil n'existe plus
                request.session.flush()
                messages.error(request, "Votre compte a été supprimé.")
                return redirect('login_user')  # Change selon ta route

        return self.get_response(request)

class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Sécuriser contre une session flushée pendant le traitement
        try:
            user_id = request.session.get("user_id")
            if user_id:
                try:
                    user = Profil.objects.get(id=user_id)
                    user.derniere_activité = timezone.now()
                    user.is_online = True
                    user.save(update_fields=["derniere_activité", "is_online"])
                except Profil.DoesNotExist:
                    pass
        except SessionInterrupted:
            # La session a été supprimée avant la fin de la requête => ignorer
            pass

        return response

        


from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from app_usercompte.models import Profil
from datetime import timedelta

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

class InactiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.session.get("user_id")

        if user_id:
            try:
                profil = Profil.objects.get(id=user_id)
                now = timezone.now()

                # 🔐 Si inactif > 30 minutes
                if profil.derniere_activité and profil.derniere_activité < now - timedelta(minutes=30):
                    profil.is_online = False
                    profil.save()
                    request.session.flush()
                    messages.warning(request, "Session expirée pour inactivité.")
                    return redirect("splash")  # ✅ vers splash

                # ✅ Sinon, mise à jour automatique
                profil.derniere_activité = now
                profil.is_online = True
                profil.save(update_fields=["derniere_activité", "is_online"])
                request.utilisateur_connecte = profil  # optionnel : dispo dans les vues

            except Profil.DoesNotExist:
                request.session.flush()
                return redirect("splash")

        return self.get_response(request)



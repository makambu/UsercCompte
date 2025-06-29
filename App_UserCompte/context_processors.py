from django.shortcuts import get_object_or_404
from .models import VideoPublier, Profil, Notification

def nouvelles_videos(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return {}
    
    try:
        profil = Profil.objects.get(id=user_id)
        non_vues = VideoPublier.objects.exclude(vus_par=profil).count()
        return {'nb_videos_non_vues': non_vues}
    except Profil.DoesNotExist:
        return {}


def base_context(request):
    nb_notifications_non_lues = 0
    utilisateur_connecte = None

    if request.session.get('user_id'):
        utilisateur_connecte = get_object_or_404(Profil, id=request.session['user_id'])
        nb_notifications_non_lues = Notification.objects.filter(
            destinataire=utilisateur_connecte,
            est_lue=False
        ).count()

    return {
        'utilisateur_connecte': utilisateur_connecte,
        'total_notices': nb_notifications_non_lues
    }




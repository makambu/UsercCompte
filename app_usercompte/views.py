from cloudinary.models import CloudinaryResource
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
import openai
from . models import *;
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import *;
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Max, Avg
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.core.serializers import serialize
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_protect
import cloudinary
import logging

logger = logging.getLogger(__name__)


def splash_view(request):
    user_id = request.session.get('user_id')

    if user_id:
        utilisateur = Profil.objects.filter(id=user_id).first()
        if utilisateur:
            return redirect('homes')  # ou autre vue principale
        else:
            # Supprime la session invalide
            request.session.flush()
            messages.error(request, "Votre compte a été supprimé. Veuillez vous reconnecter.")
            return redirect('login_user')
    return render(request, 'includ/splash.html')


def homes(request):
    user_id = request.session.get("user_id")
    reset_requested = request.GET.get('reset') == 'true'
    search_query = request.GET.get('q', '').strip()

    # Gestion reset mot de passe (POST)
    if request.method == 'POST' and request.POST.get('action') == 'reset_password':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')
        try:
            profil = Profil.objects.get(email=email)
            profil.mot_de_passe = new_password
            profil.save()
            messages.success(request, "Mot de passe mis à jour. Vous pouvez vous connecter.")
            return redirect('homes')
        except Profil.DoesNotExist:
            messages.error(request, "Email introuvable.")
            reset_requested = True

    # Utilisateur non connecté : affichage public
    if not user_id:
        utilisateurs = Profil.objects.filter(status=1).order_by('-created_on')
        if search_query:
            utilisateurs = utilisateurs.filter(Q(nom__icontains=search_query) | Q(prenom__icontains=search_query))
        return render(request, 'base.html', {
            'utilisateurs': utilisateurs,
            'search_query': search_query,
            'login_required': True,
            'reset_required': reset_requested,
        })

    # Utilisateur connecté
    try:
        utilisateur_connecte = Profil.objects.get(id=user_id)
    except Profil.DoesNotExist:
        request.session.flush()
        return redirect('login_user')

    # Vérification inactivité côté serveur (30 minutes)
    if utilisateur_connecte.derniere_activité < timezone.now() - timedelta(minutes=30):
        # Déconnexion forcée + statut hors ligne
        utilisateur_connecte.is_online = False
        utilisateur_connecte.save()
        request.session.flush()
        messages.warning(request, "Session expirée pour inactivité.")
        return redirect("login_user")

    # Mise à jour dernière activité à maintenant
    utilisateur_connecte.derniere_activité = timezone.now()
    utilisateur_connecte.is_online = True  # au cas où, le statut online est remis
    utilisateur_connecte.save()

    # Recherche utilisateurs (sauf soi)
    utilisateurs = Profil.objects.filter(status=1).exclude(id=user_id).order_by('-created_on')
    if search_query:
        utilisateurs = utilisateurs.filter(Q(nom__icontains=search_query) | Q(prenom__icontains=search_query))

    # Suppression stories expirées
    now = timezone.now()
    Story.objects.filter(expire_le__lt=now).delete()

    # Récupérer dernières stories par auteur
    latest_stories = (
        Story.objects
        .filter(expire_le__gte=now)
        .values("auteur_id")
        .annotate(latest_date=Max("date_creation"))
    )
    story_queryset = Story.objects.filter(
        expire_le__gte=now,
        date_creation__in=[item['latest_date'] for item in latest_stories]
    ).select_related('auteur')

    # Notifications non lues
    total_notices = utilisateur_connecte.notifications.filter(est_lue=False).count()

    return render(request, 'base.html', {
        'utilisateurs': utilisateurs,
        'utilisateur_connecte': utilisateur_connecte,
        'total_notices': total_notices,
        'search_query': search_query,
        'login_required': False,
        'reset_required': reset_requested,
        'stories': story_queryset,
    })

def login_user(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            user = Profil.objects.get(telephone=phone, mot_de_passe=password)
            if user.mot_de_passe == password:
                user.derniere_connexion = timezone.now()
                user.is_online = True 
                user.save()
                request.session['user_id'] = user.id
                return redirect('homes')
            else:
                messages.error(request, "Mot de passe incorrect")
        except Profil.DoesNotExist:
            messages.error(request, "Compte invalide")

    utilisateurs = Profil.objects.filter(status=1)
    return render(request, 'base.html', {'utilisateurs': utilisateurs, 'login_required': True})


def logout_user(request):
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Profil.objects.get(id=user_id)
            user.is_online = False 
            user.derniere_connexion = timezone.now()  # facultatif
            user.save()
        except Profil.DoesNotExist:
            pass

    request.session.flush()
    return redirect('homes')


@csrf_exempt  # À retirer si tu gères bien le CSRF côté JS
def logout_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'method_not_allowed'}, status=405)
    
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Profil.objects.get(id=user_id)
            user.is_online = False
            user.derniere_connexion = timezone.now()
            user.save()
            logger.info(f"Utilisateur {user_id} déconnecté via logout_ajax.")
        except Profil.DoesNotExist:
            logger.warning(f"Profil avec id {user_id} non trouvé lors du logout_ajax.")
    
    request.session.flush()
    return JsonResponse({'status': 'ok'})



def register_user(request):
    if request.method == 'POST':
        form = CompteForm(request.POST, request.FILES)
        if form.is_valid():
            profil = form.save(commit=False)
            # Hasher le mot de passe
            #from django.contrib.auth.hashers import make_password
            #profil.mot_de_passe = make_password(form.cleaned_data['mot_de_passe'])
            profil.save()
            messages.success(request, "Compte créé avec succès ! Vous pouvez vous connecter.")
            return redirect('homes')  # redirige vers la page qui montre tous les comptes
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = CompteForm()

    return render(request, 'base.html', {'form': form, 'register_required': True})



# Formulaire de demande de réinitialisation
def reset_password_home(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('new_password')

        try:
            profil = Profil.objects.get(email=email)
            profil.mot_de_passe = new_password
            profil.save()
            messages.success(request, "Mot de passe mis à jour. Veuillez vous connecter.")
            return redirect('homes')
        except Profil.DoesNotExist:
            messages.error(request, "Adresse email introuvable.")
            return redirect('/?reset=true')
        


@csrf_protect
def MyProfil(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')

    user_profil = get_object_or_404(Profil, id=user_id)
    likers = user_profil.likes.all()
    total_likes = likers.count()

    form = ProfilUpdateForm(instance=user_profil)
    form_blog = BlogForm()
    form_video = VideoForm()

    # AJAX pour modifier le profil
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = ProfilUpdateForm(request.POST, request.FILES, instance=user_profil)
        if form.is_valid():
            if 'image_profil' in request.FILES:
                ancienne_image = user_profil.image_profil
                if ancienne_image:
                    ImageHistorique.objects.create(profil=user_profil, image=ancienne_image)
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_json()})

    elif request.method == 'POST':
        if 'update_profil' in request.POST:
            form = ProfilUpdateForm(request.POST, request.FILES, instance=user_profil)
            if form.is_valid():
                if 'image_profil' in request.FILES:
                    ancienne_image = user_profil.image_profil
                    if ancienne_image:
                        ImageHistorique.objects.create(profil=user_profil, image=ancienne_image)
                form.save()
                messages.success(request, "Profil mis à jour.")
                return redirect('myProfil')
            else:
                messages.error(request, "Erreur lors de la mise à jour du profil.")

        elif 'blog_submit' in request.POST:
            form_blog = BlogForm(request.POST, request.FILES)
            if form_blog.is_valid():
                blog = form_blog.save(commit=False)
                blog.auteur = user_profil
                blog.save()
                messages.success(request, "Blog publié avec succès.")
                return redirect('myProfil')
            else:
                messages.error(request, "Erreur dans le formulaire du blog.")

        elif 'video_submit' in request.POST:
            form_video = VideoForm(request.POST)
            if form_video.is_valid():
                url = form_video.cleaned_data.get('cloudinary_url')
                if url:
                    video = VideoPublier.objects.create(
                    titre=form_video.cleaned_data['titre'],
                    description=form_video.cleaned_data['description'],
                    fichier_video=url,  # l’URL Cloudinary est stockée ici
                    auteur=user_profil
                    )
                    messages.success(request, "🎥 Vidéo uploadée avec succès.")
                else:
                    messages.error(request, "Veuillez uploader une vidéo via le bouton prévu.")
                return redirect('myProfil')
            else:
                messages.error(request, "Erreur dans le formulaire vidéo.")

    # Traitement des autres données
    blogs_user = Blog.objects.filter(auteur=user_profil).order_by('-date_creation')
    form_modifications = {blog.id: BlogFormUpdate(instance=blog) for blog in blogs_user}

    historiques = ImageHistorique.objects.filter(profil=user_profil).order_by('-date_ajout')
    paginator = Paginator(historiques, 4)
    page = request.GET.get('page_img')
    historiques_page = paginator.get_page(page)

    all_images = list(historiques)
    if user_profil.image_profil:
        all_images.insert(0, type('Obj', (object,), {'image': user_profil.image_profil, 'date_ajout': user_profil.update_on}))

    return render(request, 'User_profil.html', {
        'user_profil': user_profil,
        'form': form,
        'form_blog': form_blog,
        'form_video': form_video,
        'utilisateur_connecte': user_profil,
        'total_likes': total_likes,
        'likers': likers,
        'blogs_user': blogs_user,
        'form_modifications': form_modifications,
        'images_historiques': historiques_page,
        'all_images_profil': all_images,
    })




def ViewUser(request, id):
    user_connecte_id = request.session.get('user_id')
    if not user_connecte_id:
        return redirect('homes')

    utilisateur_connecte = get_object_or_404(Profil, id=user_connecte_id)
    user_profil = get_object_or_404(Profil, id=id)

    user_videos = VideoPublier.objects.filter(auteur=user_profil).order_by('-date_creation')
    user_blogs = Blog.objects.filter(
        auteur=user_profil,
        statut='publié'
    ).order_by('-date_creation').prefetch_related(
        Prefetch('commentaires', queryset=CommentaireBlog.objects.select_related('auteur').order_by('-date_commentaire'))
    )

    est_ami = RelationAmi.objects.filter(user1=utilisateur_connecte, user2=user_profil).exists() or \
              RelationAmi.objects.filter(user1=user_profil, user2=utilisateur_connecte).exists()

    invitation_envoyee = InvitationAmi.objects.filter(
        emetteur=utilisateur_connecte,
        recepteur=user_profil,
        statut='en_attente'
    ).exists()

    # Charger toutes les images historiques pour le carrousel
    all_images = list(ImageHistorique.objects.filter(profil=user_profil).order_by('-date_ajout'))

    # Ajouter l'image de profil actuelle comme première image si elle existe
    if user_profil.image_profil:
        from django.core.files.base import ContentFile
        from django.utils import timezone
        class TempImage:
            def __init__(self, url, date):
                self.image = type('obj', (object,), {'url': url})
                self.date_ajout = date

        all_images.insert(0, TempImage(user_profil.image_profil.url, user_profil.update_on))

    return render(request, 'View_user.html', {
        'user_profil': user_profil,
        'utilisateur_connecte': utilisateur_connecte,
        'user_blogs': user_blogs,
        'user_videos': user_videos,
        'total_likes': user_profil.likes.count(),
        'likers': user_profil.likes.all(),
        "est_ami": est_ami,
        "invitation_envoyee": invitation_envoyee,
        "all_images_profil": all_images,
    })


def aimer_profil(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Non connecté'}, status=403)

    user_profil = get_object_or_404(Profil, id=id)
    liker = get_object_or_404(Profil, id=user_id)

    liked = False

    if liker != user_profil:
        if liker in user_profil.likes.all():
            user_profil.likes.remove(liker)
            Notification.objects.filter(
                emetteur=liker,
                destinataire=user_profil,
                type="like"
            ).delete()
            liked = False
        else:
            user_profil.likes.add(liker)
            liked = True
            Notification.objects.create(
                emetteur=liker,
                destinataire=user_profil,
                message=f"{liker.nom} a aimé votre profil.",
                type="like"
            )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'nb_likes': user_profil.likes.count()
        })

    return redirect('voir_profil', id=id)


def AboutSIte(request):
    user_id = request.session.get('user_id')
    utilisateur_connecte = None
    note_posted = request.session.pop('note_posted', False)

    commentaire_form = CommentaireForm()
    probleme_form = ProblemeForm()

    if user_id:
        utilisateur_connecte = get_object_or_404(Profil, id=user_id)

    # Gestion abonnement newsletter (même les visiteurs peuvent le faire)
    if request.method == "POST" and "email_news" in request.POST:
        email = request.POST.get("email_news").strip()
        if NewsletterEmail.objects.filter(email=email).exists():
            messages.info(request, "Vous êtes déjà abonné à CGM.")
        else:
            NewsletterEmail.objects.create(email=email)
            messages.success(request, "Bienvenue ! Vous êtes maintenant abonné à CGM.")
        return redirect('AboutSIte')

    # Gestion commentaires, notes et problèmes (si utilisateur connecté)
    if request.method == "POST" and utilisateur_connecte:
        if "comment_submit" in request.POST:
            commentaire_form = CommentaireForm(request.POST)
            if commentaire_form.is_valid():
                commentaire = commentaire_form.save(commit=False)
                commentaire.user = utilisateur_connecte
                commentaire.save()
                messages.success(request, "Commentaire posté avec succès.")
                return redirect('AboutSIte')

        elif "note_submit" in request.POST:
            note_val = int(request.POST.get("note", 0))
            if note_val:
                if not Note.objects.filter(user=utilisateur_connecte).exists():
                    Note.objects.create(user=utilisateur_connecte, note=note_val)
                    request.session['note_posted'] = True
                    messages.success(request, "Merci pour votre note.")
                else:
                    messages.warning(request, "Vous avez déjà noté ce site.")
                return redirect('AboutSIte')
        
        elif "probleme_submit" in request.POST:
            probleme_form = ProblemeForm(request.POST)
            if probleme_form.is_valid():
                probleme = probleme_form.save(commit=False)
                probleme.user = utilisateur_connecte
                probleme.save()
        
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    messages.success(request, "Votre problème a été signalé. Merci !")
                    return redirect('AboutSIte')
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': probleme_form.errors})

    moyenne_note = Note.objects.aggregate(Avg('note'))['note__avg'] or 0
    commentaires = Commentaire.objects.select_related('user').order_by('-created_on')

    context = {
        'commentaire_form': commentaire_form,
        'probleme_form': probleme_form,
        'commentaires': commentaires,
        'utilisateur_connecte': utilisateur_connecte,
        'moyenne_note': round(moyenne_note, 2),
        'note_posted': note_posted,
    }

    return render(request, 'about.html', context)



def publier_blog(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')  # ou 'homes'

    user = Profil.objects.get(id=user_id)

    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.auteur = user
            blog.save()
            return redirect('myProfil')  # ou autre page
    else:
        form = BlogForm()

    return render(request, 'formulaire_blog.html', {'form': form})


def modifier_blog(request, blog_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')  # Redirige vers l'accueil si non connecté

    blog = get_object_or_404(Blog, id=blog_id, auteur__id=user_id)

    if request.method == 'POST':
        form = BlogFormUpdate(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            messages.success(request, "Le blog a été modifié avec succès.")
        else:
            messages.error(request, "Erreur lors de la modification du blog.")
    else:
        messages.error(request, "Méthode non autorisée pour cette opération.")

    return redirect('myProfil')  # Recharge la page de profil, qui contient tout


def supprimer_blog(request, blog_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')

    blog = get_object_or_404(Blog, id=blog_id, auteur__id=user_id)

    if request.method == 'POST':
        blog.delete()
        messages.success(request, "Le blog a été supprimé avec succès.")
        return redirect('myProfil')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('myProfil')



def aimer_blog(request, id):
    user_id = request.session.get('user_id')
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Non connecté'}, status=403)
        return redirect('homes')

    utilisateur = get_object_or_404(Profil, id=user_id)
    blog = get_object_or_404(Blog, id=id)

    if utilisateur in blog.likes.all():
        blog.likes.remove(utilisateur)
        liked = False
        Notification.objects.filter(
            emetteur=utilisateur,
            destinataire=blog.auteur,
            type='like',
            message__contains=blog.titre
        ).delete()
    else:
        blog.likes.add(utilisateur)
        liked = True
        if blog.auteur != utilisateur:
            Notification.objects.create(
                destinataire=blog.auteur,
                emetteur=utilisateur,
                type='like',
                message=f"{utilisateur.nom} a aimé votre blog : {blog.titre}"
            )

    # Si AJAX → renvoyer un JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'nb_likes': blog.likes.count()
        })

    # Sinon redirection normale
    redirect_url = request.META.get('HTTP_REFERER', 'blog_Views')
    return redirect(redirect_url)



@require_POST
def ajouter_commentaire(request, blog_id):
    from django.shortcuts import get_object_or_404, redirect
    from .models import Blog, CommentaireBlog, Profil
    from .models import Notification

    user_id = request.session.get('user_id')
    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Utilisateur non connecté'}, status=403)
        return redirect('homes')

    utilisateur = get_object_or_404(Profil, id=user_id)
    blog = get_object_or_404(Blog, id=blog_id)
    contenu = request.POST.get('contenu', '').strip()

    if contenu:
        commentaire = CommentaireBlog.objects.create(
            blog=blog,
            auteur=utilisateur,
            contenu=contenu
        )

        # Créer une notification si ce n’est pas l’auteur
        if blog.auteur != utilisateur:
            Notification.objects.create(
                destinataire=blog.auteur,
                emetteur=utilisateur,
                type='commentaire_blog',
                message=f"{utilisateur.nom} a commenté votre blog : {blog.titre}"
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'auteur_nom': utilisateur.nom,
                'texte': commentaire.contenu,
                'date': commentaire.date_commentaire.strftime('%d/%m/%Y %H:%M')
            })

    return redirect(request.META.get('HTTP_REFERER', 'blog_Views'))




def BlogViews(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')

    utilisateur_connecte = get_object_or_404(Profil, id=user_id)

    search_query = request.GET.get('search', '').strip()

    blogs_query = Blog.objects.filter(statut='publié').select_related('auteur').prefetch_related(
        Prefetch('commentaires', queryset=CommentaireBlog.objects.select_related('auteur').order_by('-date_commentaire'))
    )

    if search_query:
        blogs_query = blogs_query.filter(
            Q(titre__icontains=search_query) |
            Q(auteur__nom__icontains=search_query) |
            Q(auteur__prenom__icontains=search_query)
        )

    all_blogs = blogs_query.order_by('-date_creation')

    return render(request, 'blog_view.html', {
        'all_blogs': all_blogs,
        'utilisateur_connecte': utilisateur_connecte,
        'search_query': search_query,  # à afficher dans le champ input
    })

    

def notice_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_user')

    utilisateur = get_object_or_404(Profil, id=user_id)

    Notification.objects.filter(destinataire=utilisateur, est_lue=False).update(est_lue=True)

    notifications = Notification.objects.filter(destinataire=utilisateur).order_by('-date')

    invitations = InvitationAmi.objects.filter(recepteur=utilisateur, statut="envoyee").select_related("emetteur")

    return render(request, 'notices.html', {
        'utilisateur_connecte': utilisateur,
        'notifications': notifications,
        'invitations': invitations,  # 👈 nouveau
    })

def marquer_notifs_lues(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"status": "unauthorized"}, status=403)

        profil = get_object_or_404(Profil, id=user_id)
        Notification.objects.filter(recepteur=profil, lu=False).update(lu=True)
        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "invalid"}, status=400)



def liste_videos(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('homes')  # Rediriger si pas connecté

    utilisateur_connecte = get_object_or_404(Profil, id=user_id)

    search_query = request.GET.get('search', '')

    # Chargement initial avec relations
    videos = VideoPublier.objects.prefetch_related('likes', 'commentaires').order_by('-date_creation')

    # Recherche
    if search_query:
        videos = videos.filter(
            Q(titre__icontains=search_query) |
            Q(auteur__nom__icontains=search_query)
        )

    # Trouver les vidéos non vues
    videos_non_vues = videos.exclude(vus_par=utilisateur_connecte)

    # Marquer comme vues
    for video in videos_non_vues:
        video.vus_par.add(utilisateur_connecte)

    # Après mise à jour, le nombre est 0
    nb_videos_non_vues = 0

    return render(request, 'liste_videos.html', {
        'videos': videos,
        'utilisateur_connecte': utilisateur_connecte,
        'nb_videos_non_vues': nb_videos_non_vues,
        'search_query': search_query,
    })



@require_POST
def liker_video(request, video_id):
    video = get_object_or_404(VideoPublier, id=video_id)
    user_id = request.session.get('user_id')

    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Non connecté'}, status=403)
        return redirect('homes')

    user = get_object_or_404(Profil, id=user_id)
    liked = False

    if user in video.likes.all():
        video.likes.remove(user)
    else:
        video.likes.add(user)
        liked = True

        if video.auteur != user:
            Notification.objects.create(
                emetteur=user,
                destinataire=video.auteur,
                message=f"{user.nom} a aimé votre vidéo : « {video.titre} »",
                type='like_video'
            )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'nb_likes': video.likes.count()
        })

    return redirect(request.POST.get('next', 'liste_videos'))


@require_POST
def commenter_video(request, video_id):
    video = get_object_or_404(VideoPublier, id=video_id)
    user_id = request.session.get('user_id')

    if not user_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Non connecté'}, status=403)
        return redirect('homes')

    user = get_object_or_404(Profil, id=user_id)
    texte = request.POST.get('texte', '').strip()

    if texte:
        commentaire = CommentaireVideo.objects.create(
            video=video,
            user=user,
            texte=texte
        )

        if video.auteur != user:
            Notification.objects.create(
                emetteur=user,
                destinataire=video.auteur,
                message=f"{user.nom} a commenté votre vidéo : « {video.titre} »",
                type='commentaire_video'
            )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'auteur_nom': user.nom,
                'texte': commentaire.texte,
                'date': commentaire.date.strftime('%d/%m/%Y %H:%M'),
                'image_url': user.image_profil.url if user.image_profil else None,
                'profil_url': reverse('voir_profil', args=[user.id])
            })

    return redirect(request.POST.get('next', 'liste_videos'))

#-------------------- Partie Chat ------------------------

def envoyer_invitation(request, profil_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Non connecté'}, status=403)

        emetteur = get_object_or_404(Profil, id=user_id)
        recepteur = get_object_or_404(Profil, id=profil_id)

        if emetteur == recepteur:
            return JsonResponse({'success': False, 'message': 'Impossible de s’ajouter soi-même.'}, status=400)

        InvitationAmi.objects.filter(
            Q(emetteur=emetteur, recepteur=recepteur, statut='refusee') |
            Q(emetteur=recepteur, recepteur=emetteur, statut='refusee')
        ).delete()

        invitation_existante = InvitationAmi.objects.filter(
            Q(emetteur=emetteur, recepteur=recepteur, statut='envoyee') |
            Q(emetteur=recepteur, recepteur=emetteur, statut='envoyee')
        ).exists()

        if not invitation_existante:
            invitation = InvitationAmi.objects.create(emetteur=emetteur, recepteur=recepteur, statut='envoyee')

            # --- Envoi notification temps réel ---
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notif_{recepteur.id}",
                {
                    "type": "invitation_ami",
                    "invitation": {
                        "id": invitation.id,
                        "emetteur": {
                            "id": emetteur.id,
                            "nom": emetteur.nom,
                            "image": emetteur.image_profil.url if emetteur.image_profil else "",
                        },
                        "date_envoi": invitation.date_envoi.isoformat(),
                    }
                }
            )

            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Invitation déjà envoyée.'}, status=409)

    return JsonResponse({'success': False, 'message': 'Requête invalide'}, status=400)

def annuler_invitation(request, profil_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Non connecté'}, status=403)

        emetteur = get_object_or_404(Profil, id=user_id)
        recepteur = get_object_or_404(Profil, id=profil_id)

        # Annuler uniquement les invitations en attente
        invitation = InvitationAmi.objects.filter(emetteur=emetteur, recepteur=recepteur, statut='envoyee').first()

        if invitation:
            invitation.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Aucune invitation à annuler'})
    return JsonResponse({'success': False, 'message': 'Requête invalide'})


# Accepter invitation
@require_POST
def accepter_invitation(request, invitation_id):
    invitation = get_object_or_404(InvitationAmi, id=invitation_id, statut='envoyee')
    invitation.statut = 'acceptee'
    invitation.save()

    RelationAmi.objects.create(user1=invitation.emetteur, user2=invitation.recepteur)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notif_{invitation.emetteur.id}",
        {
            "type": "invitation_ami_update",
            "invitation_id": invitation.id,
            "statut": invitation.statut,
        }
    )
    async_to_sync(channel_layer.group_send)(
        f"notif_{invitation.recepteur.id}",
        {
            "type": "invitation_ami_update",
            "invitation_id": invitation.id,
            "statut": invitation.statut,
        }
    )

    # Optionnel : données de l'ami côté connecté
    user_id = request.session.get("user_id")
    ami = invitation.emetteur if invitation.recepteur.id == user_id else invitation.recepteur

    ami_data = {
        "id": ami.id,
        "nom": ami.nom,
        "prenom": ami.prenom,
        "image": ami.image_profil.url if ami.image_profil else "",
    }

    return JsonResponse({
        'status': 'ok',
        'message': "Invitation acceptée.",
        'ami': ami_data
    })


# Refuser invitation
@require_POST
def refuser_invitation(request, invitation_id):
    invitation = get_object_or_404(InvitationAmi, id=invitation_id, statut='envoyee')
    invitation.statut = 'refusee'
    invitation.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notif_{invitation.emetteur.id}",
        {
            "type": "invitation_ami_update",
            "invitation_id": invitation.id,
            "statut": invitation.statut,
        }
    )
    async_to_sync(channel_layer.group_send)(
        f"notif_{invitation.recepteur.id}",
        {
            "type": "invitation_ami_update",
            "invitation_id": invitation.id,
            "statut": invitation.statut,
        }
    )

    ami_id = invitation.emetteur.id if request.session.get("user_id") == invitation.recepteur.id else invitation.recepteur.id

    return JsonResponse({
        'status': 'ok',
        'message': "Invitation refusée.",
        'ami_id': ami_id
    })


@require_POST
def bloquer_ami(request, ami_id):
    utilisateur = get_object_or_404(Profil, id=request.session.get("user_id"))
    ami = get_object_or_404(Profil, id=ami_id)

    # Logique : supprimer la relation et ajouter à liste des bloqués si tu as une table
    RelationAmi.objects.filter(
        Q(user1=utilisateur, user2=ami) | Q(user1=ami, user2=utilisateur)
    ).delete()

    # Ici tu peux créer une table Blocage si tu veux conserver l'info
    return JsonResponse({"status": "ok"})


def mes_amis(request):
    user_id = request.session.get("user_id")
    utilisateur = get_object_or_404(Profil, id=user_id)

    # Invitations reçues (pagination)
    invitations_queryset = InvitationAmi.objects.filter(recepteur=utilisateur, statut='envoyee').order_by('-id')
    total_invitations = invitations_queryset.count()
    invitation_paginator = Paginator(invitations_queryset, 3)
    invitation_page = request.GET.get('page_inv')
    invitations_recues = invitation_paginator.get_page(invitation_page)

    # Liste des amis (pagination)
    relations1 = RelationAmi.objects.filter(user1=utilisateur).values_list('user2_id', flat=True)
    relations2 = RelationAmi.objects.filter(user2=utilisateur).values_list('user1_id', flat=True)
    amis_ids = list(set(relations1).union(set(relations2)))
    amis_list = Profil.objects.filter(id__in=amis_ids).order_by('nom', 'prenom')
    total_amis = amis_list.count()
    amis_paginator = Paginator(amis_list, 5)
    amis_page = request.GET.get('page_amis')
    amis = amis_paginator.get_page(amis_page)

    context = {
        "utilisateur_connecte": utilisateur,
        "invitations_recues": invitations_recues,
        "total_invitations": total_invitations,
        "amis": amis,
        "total_amis": total_amis,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "amis_liste.html", context)

    return render(request, "User_profil.html", context)


def amis_du_user(request, id):
    user_cible = get_object_or_404(Profil, id=id)

    relations1 = RelationAmi.objects.filter(user1=user_cible).values_list('user2_id', flat=True)
    relations2 = RelationAmi.objects.filter(user2=user_cible).values_list('user1_id', flat=True)
    amis_ids = list(set(relations1).union(set(relations2)))

    amis = Profil.objects.filter(id__in=amis_ids).order_by('nom', 'prenom')

    paginator = Paginator(amis, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("amis_du_user_list.html", {
            'amis': page_obj,
            'user_cible': user_cible,
            'total_amis': len(amis_ids)  # ← on ajoute ça
        }, request=request)
        return JsonResponse({"html": html})

    return JsonResponse({"error": "Requête invalide"}, status=400)



def chat_view(request, user_id):
    user_connecte = get_object_or_404(Profil, id=request.session.get('user_id'))
    user_cible = get_object_or_404(Profil, id=user_id)

    # Marquer messages comme lus + notifie=True (pour badge notif)
    Message.objects.filter(
        expediteur=user_cible,
        destinataire=user_connecte,
        lu=False
    ).update(lu=True, notifie=True)

    messages = Message.objects.filter(
        Q(expediteur=user_connecte, destinataire=user_cible) |
        Q(expediteur=user_cible, destinataire=user_connecte)
    ).order_by("date_envoi")

    en_ligne = getattr(user_cible, "is_online", False)  # Sécurité au cas où

    return render(request, "chat_solola/chat_page.html", {
        'utilisateur_connecte': user_connecte,
        'user_cible': user_cible,
        'messages': messages,
        'en_ligne': en_ligne,
    })


@csrf_exempt
def send_message_ajax(request):
    if request.method == "POST":
        expediteur_id = request.session.get('user_id')
        destinataire_id = request.POST.get("destinataire_id")
        contenu = request.POST.get("contenu", "").strip()
        fichier = request.FILES.get("fichier")

        if not expediteur_id or not destinataire_id:
            return JsonResponse({"status": "error", "message": "Paramètres manquants"}, status=400)

        expediteur = get_object_or_404(Profil, id=expediteur_id)
        destinataire = get_object_or_404(Profil, id=destinataire_id)

        fichier_cloudinary = None
        type_fichier = None

        if fichier:
            result = cloudinary.uploader.upload_large(
                fichier,
                resource_type="auto",
                folder="chat_fichiers/"
            )

            public_id = result.get("public_id")
            resource_type = result.get("resource_type")

            fichier_cloudinary = CloudinaryResource(public_id=public_id, resource_type=resource_type)

            content_type = fichier.content_type.lower()
            if content_type.startswith("image"):
                type_fichier = "image"
            elif content_type.startswith("video"):
                type_fichier = "video"
            elif "pdf" in content_type:
                type_fichier = "pdf"
            elif "word" in content_type:
                type_fichier = "doc"
            elif "excel" in content_type or "sheet" in content_type:
                type_fichier = "xls"
            else:
                type_fichier = "autre"

        msg = Message.objects.create(
            expediteur=expediteur,
            destinataire=destinataire,
            contenu=contenu,
            fichier=fichier_cloudinary,
            type_fichier=type_fichier
        )

        return JsonResponse({
            "status": "ok",
            "contenu": msg.contenu,
            "fichier_url": msg.fichier.url if msg.fichier else "",
            "type_fichier": msg.type_fichier
        })

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

def liste_conversations(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('login_user')  # redirection si session vide

    try:
        utilisateur = Profil.objects.get(id=user_id)
    except Profil.DoesNotExist:
        request.session.flush()  # session invalide
        return redirect('login_user')

    # Récupérer tous les messages envoyés ou reçus
    messages = Message.objects.filter(
        Q(expediteur=utilisateur) | Q(destinataire=utilisateur)
    )

    user_ids = set(messages.values_list('expediteur_id', flat=True)) | set(messages.values_list('destinataire_id', flat=True))
    user_ids.discard(utilisateur.id)

    conversations = Profil.objects.filter(id__in=user_ids)

    last_messages = {}
    messages_non_lus = {}

    for user in conversations:
        last_msg = Message.objects.filter(
            Q(expediteur=utilisateur, destinataire=user) |
            Q(expediteur=user, destinataire=utilisateur)
        ).order_by("-date_envoi").first()

        if last_msg:
            last_messages[user.id] = last_msg
            if last_msg.destinataire == utilisateur and not last_msg.lu:
                messages_non_lus[user.id] = True

    sorted_conversations = sorted(
        conversations,
        key=lambda u: last_messages.get(u.id).date_envoi if last_messages.get(u.id) else None,
        reverse=True
    )

    en_ligne_ids = list(
        Profil.objects.filter(is_online=True).values_list('id', flat=True)
    )

    return render(request, "chat_solola/liste_conversations.html", {
        "utilisateur_connecte": utilisateur,
        "conversations": sorted_conversations,
        "last_messages": last_messages,
        "messages_non_lus": messages_non_lus,
        "en_ligne_ids": en_ligne_ids,
    })


def verifier_messages_non_lus(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"status": "non_connecte"})

    profil = get_object_or_404(Profil, id=user_id)
    limite = timezone.now() - timedelta(minutes=5)

    messages = Message.objects.filter(
        destinataire=profil,
        lu=False,
        notifie=False,
        date_envoi__lte=limite
    )

    if messages.exists():
        # Marquer comme notifié pour ne pas jouer le son plusieurs fois
        messages.update(notifie=True)
        return JsonResponse({"status": "jouer_sonnerie"})

    return JsonResponse({"status": "ok"})


def compteur_messages_non_lus(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"nb": 0})

    profil = get_object_or_404(Profil, id=user_id)
    nb = Message.objects.filter(destinataire=profil, lu=False).count()

    return JsonResponse({"nb": nb})



def ajouter_story(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("homes")

    profil = get_object_or_404(Profil, id=user_id)

    if request.method == 'POST':
        image = request.FILES.get("image")
        video = request.FILES.get("video")

        if image or video:
            Story.objects.create(
                auteur=profil,
                image=image if image else None,
                video=video if video else None,
                expire_le=timezone.now() + timedelta(hours=24)
            )
            return redirect("homes")

    return render(request, "story/ajouter_story.html", {
        "utilisateur_connecte": profil
    })


def stories_utilisateur(request, user_id):
    now = timezone.now()

    # Supprimer les stories expirées automatiquement
    Story.objects.filter(expire_le__lt=now).delete()

    stories = Story.objects.filter(
        auteur_id=user_id,
        expire_le__gte=now
    ).order_by("date_creation")

    user_connecte_id = request.session.get("user_id")
    user_connecte = get_object_or_404(Profil, id=user_connecte_id) if user_connecte_id else None

    story_data = []
    for story in stories:
        story_data.append({
            "id": story.id,
            "type": story.get_type(),
            "media_url": story.get_media_url(),
            "description": getattr(story, "description", ""),
            "date": story.date_creation.strftime("%d/%m/%Y %H:%M"),
            "likes": story.likes.count(),
            "is_liked": user_connecte in story.likes.all() if user_connecte else False
        })

    auteur = get_object_or_404(Profil, id=user_id)
    image_profil = auteur.image_profil.url if auteur.image_profil else static("images/image_4.png")

    return JsonResponse({
        "stories": story_data,
        "nom": f"{auteur.nom} {auteur.prenom}",
        "image_profil": image_profil,
        "est_proprietaire": user_connecte_id == auteur.id
    })

@csrf_exempt
def like_story(request, story_id):
    user_id = request.session.get("user_id")
    if not user_id or request.method != "POST":
        return JsonResponse({"success": False}, status=403)

    story = get_object_or_404(Story, id=story_id)
    profil = get_object_or_404(Profil, id=user_id)

    if profil in story.likes.all():
        story.likes.remove(profil)
        is_liked = False
    else:
        story.likes.add(profil)
        is_liked = True

    return JsonResponse({
        "success": True,
        "is_liked": is_liked,
        "total_likes": story.likes.count()
    })


def story_likes_list(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    users = story.likes.all()
    data = [{
        "nom": f"{u.nom} {u.prenom}",
        "image": u.image_profil.url if u.image_profil else static("images/image_4.png")
    } for u in users]
    return JsonResponse({"users": data})

def notifier_amis_story(utilisateur):
    # Récupérer les amis du profil
    amis_1 = RelationAmi.objects.filter(user1=utilisateur).values_list('user2', flat=True)
    amis_2 = RelationAmi.objects.filter(user2=utilisateur).values_list('user1', flat=True)
    amis_ids = set(list(amis_1) + list(amis_2))

    for ami_id in amis_ids:
        Notification.objects.create(
            emetteur=utilisateur,
            destinataire_id=ami_id,
            message="a publié une nouvelle story.",
            type="nouvelle_story",
            date=timezone.now()
        )




@csrf_exempt
def ajouter_story_ajax(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"status": "error", "message": "Non connecté."}, status=401)

    utilisateur = get_object_or_404(Profil, id=user_id)

    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
                video_url = data.get("video_url")

                if video_url:
                    Story.objects.create(
                        auteur=utilisateur,
                        video=video_url,
                        expire_le=timezone.now() + timedelta(hours=24)
                    )
                    return JsonResponse({"status": "success", "message": "Story vidéo enregistrée."})
                else:
                    return JsonResponse({"status": "error", "message": "URL vidéo manquante."})
            else:
                image = request.FILES.get("image")
                if image:
                    Story.objects.create(
                        auteur=utilisateur,
                        image=image,
                        expire_le=timezone.now() + timedelta(hours=24)
                    )
                    return JsonResponse({"status": "success", "message": "Story image enregistrée."})
                else:
                    return JsonResponse({"status": "error", "message": "Aucun fichier fourni."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Méthode non autorisée"}, status=405)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chatbot_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('homes')

    utilisateur = get_object_or_404(Profil, id=user_id)
    return render(request, "chat_solola/chatbot.html", {
        "utilisateur_connecte": utilisateur,
    })

@csrf_protect
def envoyer_question(request):
    if request.method == "POST":
        return JsonResponse({
            "response": "💡 La fonctionnalité IA est temporairement désactivée. Elle sera bientôt disponible."
        })

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


def charger_historique(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Non connecté"}, status=403)

    utilisateur = get_object_or_404(Profil, id=user_id)
    messages = MessageIA.objects.filter(utilisateur=utilisateur).order_by('-date')[:20]

    data = [{
        "question": m.question,
        "reponse": m.reponse
    } for m in messages]

    return JsonResponse({"messages": data})


def nom_utilisateur(request, user_id):
    try:
        profil = Profil.objects.get(id=user_id)
        last_msg = Message.objects.filter(expediteur=profil).order_by("-date_envoi").first()
        return JsonResponse({
            "nom": f"{profil.nom} {profil.prenom}",
            "last_message": last_msg.contenu[:100] if last_msg and last_msg.contenu else ""
        })
    except Profil.DoesNotExist:
        return JsonResponse({"nom": "Inconnu", "last_message": ""})







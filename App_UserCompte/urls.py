from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.splash_view, name='splash'),  # Page d’accueil temporaire
    path('homes/', views.homes, name='homes'),  # ta page d’accueil normale
    path('login_user/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register_user'),
    path('reset-password-home/', views.reset_password_home, name='reset_password_home'),
    path('myProfil/', views.MyProfil, name='myProfil'),
    path('voir_profil/<int:id>/', views.ViewUser, name='voir_profil'),
    path('aimer_profil/<int:id>/', views.aimer_profil, name='aimer_profil'),
    path('about/', views.AboutSIte, name='AboutSIte'),
    path('publier_blog/', views.publier_blog, name='publier_blog'),
    path('blog/modifier/<int:blog_id>/', views.modifier_blog, name='modifier_blog'),
    path('blog/supprimer/<int:blog_id>/', views.supprimer_blog, name='supprimer_blog'),
    path('aimer_blog/<int:id>/', views.aimer_blog, name='aimer_blog'),
    path('commenter/<int:blog_id>/', views.ajouter_commentaire, name='ajouter_commentaire'),
    path('blog_Views/', views.BlogViews, name='blog_Views'),
    path('notice/', views.notice_view, name='notice_view'),
    path('videos/', views.liste_videos, name='liste_videos'),
    path('videos/<int:video_id>/like/', views.liker_video, name='liker_video'),
    path('videos/<int:video_id>/comment/', views.commenter_video, name='commenter_video'),
    path('logout_ajax/', views.logout_ajax, name='logout_ajax'),
    path('ajouter-ami/<int:profil_id>/', views.envoyer_invitation, name='envoyer_invitation'),
    path('annuler-invitation/<int:profil_id>/', views.annuler_invitation, name='annuler_invitation'),
    path('invitation-accepter/<int:invitation_id>/', views.accepter_invitation, name='accepter_invitation'),
    path('invitation-refuser/<int:invitation_id>/', views.refuser_invitation, name='refuser_invitation'),
    path("bloquer-ami/<int:ami_id>/", views.bloquer_ami, name="bloquer_ami"),
    path('mes-amis/', views.mes_amis, name='mes_amis'),
    path('user-amis/<int:id>/', views.amis_du_user, name='amis_du_user'),
    path("chat/<int:user_id>/", views.chat_view, name="chat_user"),
    path("send-message/", views.send_message_ajax, name="send_message_ajax"),
    path("chat/", views.liste_conversations, name="messagerie"),
    path('story/ajouter/', views.ajouter_story, name='ajouter_story'),
    path('ajax/stories/<int:user_id>/', views.stories_utilisateur, name='ajax_stories_user'),
    path('ajax/story/ajouter/', views.ajouter_story_ajax, name='ajax_ajouter_story'),
    path("ajax/story/<int:story_id>/like/", views.like_story, name="like_story"),
    path("ajax/story/<int:story_id>/likes/", views.story_likes_list, name="story_likes_list"),
    path('chatbot/', views.chatbot_view, name='chatbot_view'),
    path("chatbot/api/", views.envoyer_question, name="chatbot_api"),
    path("chatbot/historique/", views.charger_historique, name="chatbot_historique"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

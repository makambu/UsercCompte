from django.contrib import admin
from .models import *;

# Register your models here.

admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'sexe', 'mot_de_passe', 'created_on', 'status')
    search_fields = ('nom', 'prenom', 'telephone')
    list_filter = ('sexe', 'status')

admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('titre', 'image', 'auteur', 'statut', 'slug', 'date_creation', 'date_modification')
    search_fields = ('titre', 'auteur', 'statut')
    list_filter = ('titre', 'auteur', 'statut')

admin.register(InvitationAmi)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['emetteur', 'recepteur', 'statut', 'date_envoi']
    list_filter = ['statut']
    search_fields = ['emetteur__nom', 'recepteur__nom']
    fields = ['emetteur', 'recepteur', 'statut']

admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ['user', 'commentaire', 'created_on']
    list_filter = ['user']
    search_fields = ['user', 'created_on']
    fields = ['user', 'commentaire']

admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'note', 'date']
    list_filter = ['user']
    search_fields = ['user', 'note']
    fields = ['user', 'date']

admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'note', 'date']
    list_filter = ['user']
    search_fields = ['user', 'note']
    fields = ['user', 'date']


admin.register(NewsletterEmail)
class NewsletterEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'date_soumission']
    list_filter = ['email']
    search_fields = ['email']
    fields = ['email', 'date_soumission']

admin.register(Probleme)
class ProblemeAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'date_signalee']
    list_filter = ['user']
    search_fields = ['user']
    fields = ['user', 'message', 'date_signalee']

admin.register(RelationAmi)
class RelationAmiAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'date_relation']
    list_filter = ['user1', 'user2']
    search_fields = ['user1__nom', 'user2__nom']
    fields = ['user1', 'user2', 'date_relation']




admin.site.register(Profil, ProfilAdmin)
admin.site.register(Commentaire, CommentaireAdmin)
admin.site.register(Note, NoteAdmin)
admin.site.register(NewsletterEmail, NewsletterEmailAdmin)
admin.site.register(Probleme, ProblemeAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(CommentaireBlog)
admin.site.register(CommentaireVideo)
admin.site.register(Notification)
admin.site.register(VideoPublier)
admin.site.register(InvitationAmi, InvitationAdmin)
admin.site.register(RelationAmi, RelationAmiAdmin)
admin.site.register(Message)
admin.site.register(ImageHistorique)
admin.site.register(MessageIA)
admin.site.register(Story)

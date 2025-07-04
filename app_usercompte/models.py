from django.db import models
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


# Create your models here.

STATUS = ((0, "Draft"), (1, "Published"))

class Profil(models.Model):
    HOMME = 'H'
    FEMME = 'F'

    SEXE_CHOICES = [
        (HOMME, 'Homme'),
        (FEMME, 'Femme'),
    ]

    nom = models.CharField(max_length=150, null=True, blank=True)
    post_nom = models.CharField(max_length=150, null=True, blank=True)
    prenom = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    mot_de_passe = models.CharField(max_length=128, null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, default=HOMME)
    profession = models.CharField(max_length=250, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_nais = models.CharField(max_length=250, blank=True, null=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    pays = models.CharField(max_length=100, blank=True)
    biographie = models.TextField(null=True, blank=True)
    image_profil = CloudinaryField('image', folder='profils/', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    update_on = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=STATUS, default=1)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    derniere_activité = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)  # Nouveau champ
    likes = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='liked_by')

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        nom = self.nom or ""
        prenom = self.prenom or ""
        return f"{prenom} {nom}".strip() or "Profil"


class ImageHistorique(models.Model):
    profil = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name="images_historiques")
    image = CloudinaryField('image', folder='historique_profils/', blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-date_ajout']

    def __str__(self):
        return f"Ancienne image de {self.profil.nom or ''} {self.profil.prenom or ''}"



class Commentaire(models.Model):
    user = models.ForeignKey(Profil, on_delete=models.CASCADE)
    commentaire = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.user.nom}"

class Note(models.Model):
    user = models.OneToOneField(Profil, on_delete=models.CASCADE)
    note = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.nom} - {self.note} étoiles"

class NewsletterEmail(models.Model):
    email = models.EmailField(unique=True)
    date_soumission = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
class Probleme(models.Model):
    user = models.ForeignKey(Profil, on_delete=models.CASCADE)
    message = models.TextField()
    date_signalee = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"Problème de {self.user.nom} le {self.date_signalee.strftime('%d/%m/%Y')}"
    

class Blog(models.Model):
    STATUT_CHOICES = [
        ('publié', 'Publié'),
        ('brouillon', 'Brouillon'),
    ]

    auteur = models.ForeignKey('Profil', on_delete=models.CASCADE, related_name='blogs')
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    image = CloudinaryField('image', folder='blogs/', blank=True, null=True)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    slug = models.SlugField(unique=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(Profil, related_name='blogs_aimés', blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titre)
            slug = base_slug
            num = 1
            while Blog.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{num}'
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.titre
    
class CommentaireBlog(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_commentaire = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commentaire de {self.auteur.nom}"


class Notification(models.Model):
    emetteur = models.ForeignKey(Profil, related_name='notifications_emises', on_delete=models.CASCADE)
    destinataire = models.ForeignKey(Profil, related_name='notifications', on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    est_lue = models.BooleanField(default=False)
    type = models.CharField(max_length=50, blank=True, null=True)


class VideoPublier(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    fichier_video = CloudinaryField(
        'video', folder='videos/', upload_preset='video_large', blank=True, null=True
    )
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='videos')
    date_creation = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(Profil, related_name='videos_aimees', blank=True)
    vus_par = models.ManyToManyField(Profil, related_name='videos_vues', blank=True)

    def __str__(self):
        return self.titre

    def nombre_likes(self):
        return self.likes.count()

    

class CommentaireVideo(models.Model):
    video = models.ForeignKey(VideoPublier, on_delete=models.CASCADE, related_name='commentaires')
    user = models.ForeignKey(Profil, on_delete=models.CASCADE)
    texte = models.TextField(max_length=500)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Commentaire de {self.user.nom} sur {self.video.titre}"


class InvitationAmi(models.Model):
    emetteur = models.ForeignKey('Profil', related_name='invitations_envoyees', on_delete=models.CASCADE)
    recepteur = models.ForeignKey('Profil', related_name='invitations_recues', on_delete=models.CASCADE)
    date_envoi = models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=[('envoyee', 'Envoyée'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée')], default='envoyee')

    class Meta:
        unique_together = ('emetteur', 'recepteur')

class RelationAmi(models.Model):
    user1 = models.ForeignKey('Profil', related_name='ami_1', on_delete=models.CASCADE)
    user2 = models.ForeignKey('Profil', related_name='ami_2', on_delete=models.CASCADE)
    date_relation = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user1', 'user2')


class Message(models.Model):
    expediteur = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='messages_recus')
    contenu = models.TextField(blank=True)
    fichier = CloudinaryField('file', folder='chat_fichiers/', null=True, blank=True)
    type_fichier = models.CharField(max_length=10, null=True, blank=True)  # "image", "video", "pdf", etc.
    date_envoi = models.DateTimeField(default=timezone.now)
    lu = models.BooleanField(default=False)
    notifie = models.BooleanField(default=False)

    def __str__(self):
        return f"De {self.expediteur} à {self.destinataire}"



class MessageIA(models.Model):
    utilisateur = models.ForeignKey(Profil, on_delete=models.CASCADE, related_name='conversations')
    question = models.TextField()
    reponse = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.utilisateur.nom} - {self.date.strftime('%d/%m/%Y %H:%M')}"



def get_expiration_date():
    return timezone.now() + timedelta(hours=24)


class Story(models.Model):
    auteur = models.ForeignKey(Profil, on_delete=models.CASCADE)
    image = CloudinaryField('image', folder='stories/images/', null=True, blank=True)
    video = CloudinaryField('video', folder='stories/videos/', resource_type='video', null=True, blank=True)
    likes = models.ManyToManyField(Profil, related_name='story_likes', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField(default=get_expiration_date)

    def __str__(self):
        return f"Story de {self.auteur.nom} - {self.date_creation}"

    def get_media_url(self):
        if self.image:
            return self.image.url
        elif self.video:
            return self.video.url if hasattr(self.video, 'url') else str(self.video)
        return ""

    def get_type(self):
        if self.video:
            return "video"
        elif self.image:
            return "image"
        return "unknown"
    
    def get_mime_type(self):
        if self.video:
            url = self.video.url
            if url.endswith(".mp4"):
                return "video/mp4"
            elif url.endswith(".webm"):
                return "video/webm"
            elif url.endswith(".mov"):
                return "video/quicktime"
        return "video/mp4"






from django import forms
from .models import *;

class LoginForm(forms.ModelForm):

    class Meta:
        model = Profil
        fields = ['telephone', 'mot_de_passe',]


class CompteForm(forms.ModelForm):
    mot_de_passe = forms.CharField(
        required=True,  # ← Ajout ici
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
    )

    class Meta:
        model = Profil
        fields = ['nom', 'prenom', 'sexe', 'telephone', 'mot_de_passe', 'image_profil']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['nom'].required = True
        self.fields['prenom'].required = True
        self.fields['sexe'].required = True
        self.fields['telephone'].required = True
        #self.fields['image_profil'].required = True  # ← même pour l’image

        self.fields['nom'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })

        self.fields['prenom'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })

        self.fields['sexe'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose your gender'
        })

        self.fields['telephone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your phone'
        })

        self.fields['image_profil'].widget.attrs.update({
            'class': 'form-control'
        })


class ProfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ['nom', 'post_nom', 'prenom', 'sexe', 'telephone', 'email', 'profession',
                  'date_naissance', 'lieu_nais', 'pays', 'ville', 'biographie', 'image_profil']



class CommentaireForm(forms.ModelForm):
    class Meta:
        model = Commentaire
        fields = ['commentaire']
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Votre commentaire ici...'
            })
        }

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['note']

class ProblemeForm(forms.ModelForm):
    class Meta:
        model = Probleme
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Décrivez le problème ici...'
            })
        }




class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titre', 'contenu', 'image', 'statut']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du blog'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description du blog...', 'rows': 5}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }

class BlogFormUpdate(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titre', 'image', 'contenu', 'statut']

class VideoForm(forms.ModelForm):
    class Meta:
        model = VideoPublier
        fields = ['titre', 'description', 'fichier_video']
        widgets = {
            'titre': forms.TextInput(attrs={
                'placeholder': 'Entrer le titre de la vidéo',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Ajoutez une description claire de la vidéo...',
                'class': 'form-control',
                'rows': 3,
            }),
            'fichier_video': forms.ClearableFileInput(attrs={
                'accept': 'video/*',
                'onchange': 'previewVideo(event)',
                'class': 'form-control'
            }),
        }

    def clean_fichier_video(self):
        video = self.cleaned_data.get('fichier_video')
        if video:
            if not video.content_type.startswith('video'):
                raise forms.ValidationError("Veuillez insérer un fichier vidéo uniquement.")
            if video.size > 100 * 1024 * 1024:  # 100 Mo max
                raise forms.ValidationError("La vidéo ne doit pas dépasser 100 Mo.")
        return video



class CommentaireVideoForm(forms.ModelForm):
    class Meta:
        model = CommentaireVideo
        fields = ['texte']
        widgets = {
            'texte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ajouter un commentaire...',
            }),
        }






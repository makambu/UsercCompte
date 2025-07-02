from django.core.management.base import BaseCommand
from cloudinary.uploader import upload
from app_usercompte.models import Profil, ImageHistorique, Story, VideoPublier, Blog, Message
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Migrate existing local media files to Cloudinary'

    def handle(self, *args, **options):
        def upload_and_update(obj, field_name, folder):
            file_field = getattr(obj, field_name)
            if file_field and not str(file_field.url).startswith("http"):
                local_path = os.path.join(settings.MEDIA_ROOT, str(file_field))
                if os.path.isfile(local_path):
                    try:
                        result = upload(local_path, folder=folder)
                        setattr(obj, field_name, result['secure_url'])
                        obj.save()
                        self.stdout.write(self.style.SUCCESS(f'{field_name} migré : {local_path}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Erreur: {e}'))

        for profil in Profil.objects.all():
            upload_and_update(profil, 'image_profil', 'profils')

        for img in ImageHistorique.objects.all():
            upload_and_update(img, 'image', 'historique_profils')

        for story in Story.objects.all():
            upload_and_update(story, 'image', 'stories/images')
            upload_and_update(story, 'video', 'stories/videos')

        for video in VideoPublier.objects.all():
            upload_and_update(video, 'fichier_video', 'videos')

        for blog in Blog.objects.all():
            upload_and_update(blog, 'image', 'blogs')

        for message in Message.objects.all():
            upload_and_update(message, 'fichier', 'chat_fichiers')

        self.stdout.write(self.style.SUCCESS('Migration terminée.'))

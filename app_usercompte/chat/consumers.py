import json
import base64
import uuid
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from app_usercompte.models import Profil, Message
import cloudinary

logger = logging.getLogger(__name__)

def decode_base64_file(data, filename):
    try:
        format, file_str = data.split(';base64,')
        file_str += '=' * (-len(file_str) % 4)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        return ContentFile(base64.b64decode(file_str), name=unique_name)
    except Exception as e:
        logger.error(f"Erreur de décodage base64 : {str(e)}")
        raise

# ====================================
# ✅ ChatConsumer (pour chat socket)
# ====================================
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user_id = self.scope["user"].id if self.scope["user"].is_authenticated else None

        # Joindre le groupe chat
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Joindre le groupe notification spécifique utilisateur
        if self.user_id:
            await self.channel_layer.group_add(f"notif_{self.user_id}", self.channel_name)
            logger.info(f"[CONNECT CHAT] Connecté à notif_{self.user_id}")

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.user_id:
            await self.channel_layer.group_discard(f"notif_{self.user_id}", self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        logger.info(f"[RECEIVE CHAT] : {data}")

        # Marquer messages lus
        if data.get("type") == "messages_read":
            await sync_to_async(
                Message.objects.filter(
                    expediteur_id=data["destinataire_id"],
                    destinataire_id=data["expediteur_id"],
                    lu=False
                ).update
            )(lu=True)
            await self.channel_layer.group_send(
                f"notif_{data['expediteur_id']}",
                {"type": "remove_notification", "from_id": data["destinataire_id"]}
            )
            return

        expediteur_id = data.get("expediteur_id")
        destinataire_id = data.get("destinataire_id")
        expediteur_nom = data.get("expediteur_nom")
        if not (expediteur_id and destinataire_id and expediteur_nom):
            return

        expediteur = await sync_to_async(Profil.objects.get)(id=expediteur_id)
        destinataire = await sync_to_async(Profil.objects.get)(id=destinataire_id)

        # Message texte
        if "message" in data:
            msg = await sync_to_async(Message.objects.create)(
                expediteur=expediteur,
                destinataire=destinataire,
                contenu=data["message"]
            )
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": msg.contenu,
                    "expediteur": expediteur_nom,
                    "expediteur_id": expediteur_id,
                }
            )
            # Notification pour destinataire
            await self.channel_layer.group_send(
                f"notif_{destinataire_id}",
                {
                    "type": "new_notification",
                    "from_id": expediteur_id
                }
            )

        # Message fichier
        elif "file" in data:
            try:
                decoded_file = decode_base64_file(data["file"], data["file_name"])

                # Utiliser upload_large pour les gros fichiers
                upload_result = await sync_to_async(cloudinary.uploader.upload_large)(
                    decoded_file,
                    folder="chat_fichiers/",
                    resource_type="auto"
                )

                public_id = upload_result.get("public_id")
                resource_type = upload_result.get("resource_type")
                secure_url = upload_result.get("secure_url")
                file_format = upload_result.get("format", "").lower()

                # Détermination du type_fichier pour affichage
                if resource_type == "image":
                    type_fichier = "image"
                elif resource_type == "video":
                    type_fichier = "video"
                elif file_format == "pdf":
                    type_fichier = "pdf"
                elif file_format in ["doc", "docx"]:
                    type_fichier = "doc"
                elif file_format in ["xls", "xlsx", "csv"]:
                    type_fichier = "xls"
                else:
                    type_fichier = "autre"

                # Création du Message avec un CloudinaryResource (compatible CloudinaryField)
                from cloudinary.models import CloudinaryResource
                fichier_cloudinary = CloudinaryResource(public_id=public_id, resource_type=resource_type)

                msg = await sync_to_async(Message.objects.create)(
                    expediteur=expediteur,
                    destinataire=destinataire,
                    contenu="",
                    fichier=fichier_cloudinary,
                    type_fichier=type_fichier
                )

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": "",
                        "expediteur": expediteur_nom,
                        "expediteur_id": expediteur_id,
                        "file_url": secure_url,
                        "file_name": data["file_name"],
                        "file_ext": file_format,
                    }
                )

                # Notification
                await self.channel_layer.group_send(
                    f"notif_{destinataire_id}",
                    {
                        "type": "new_notification",
                        "from_id": expediteur_id
                    }
                )
            except Exception as e:
                logger.error(f"[FILE ERROR] {str(e)}")

        # Appel vocal - démarrage
        elif data.get("type") == "call_start":
            await self.channel_layer.group_send(
                f"notif_{destinataire_id}",
                {
                    "type": "call_incoming",
                    "from_id": expediteur_id,
                    "from_name": expediteur_nom,
                }
            )

        # Appel - réponse
        elif data.get("type") == "call_answer":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_answered",
                    "answer": data["answer"],
                    "from_id": expediteur_id,
                }
            )

        # Appel - fin
        elif data.get("type") == "call_end":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "call_ended",
                    "from_id": expediteur_id,
                }
            )

        # Appel manqué
        elif data.get("type") == "call_missed":
            await sync_to_async(Message.objects.create)(
                expediteur=expediteur,
                destinataire=destinataire,
                contenu=f"📞 Appel en absence de {expediteur.nom}"
            )

    # Envois WebSocket client (Chat)
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def call_answered(self, event):
        await self.send(text_data=json.dumps(event))

    async def call_ended(self, event):
        await self.send(text_data=json.dumps(event))

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_message_notification",
            "from_id": event["from_id"]
        }))

    async def remove_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "remove_message_notification",
            "from_id": event["from_id"]
        }))

    async def call_incoming(self, event):
        await self.send(text_data=json.dumps({
            "type": "call_incoming",
            "from_id": event["from_id"],
            "from_name": event["from_name"]
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["session"].get("user_id")
        if not self.user_id:
            await self.close()
            return

        self.group_name = f"notif_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info(f"[NOTIF] Connexion socket notif_{self.user_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def invitation_ami(self, event):
        await self.send(text_data=json.dumps({
            "type": "invitation_ami",
            "invitation": event["invitation"]
        }))

    async def invitation_ami_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "invitation_ami_update",
            "invitation_id": event["invitation_id"],
            "statut": event["statut"],
        }))

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_message_notification",
            "from_id": event["from_id"]
        }))

    async def remove_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "remove_message_notification",
            "from_id": event["from_id"]
        }))

    async def call_incoming(self, event):
        await self.send(text_data=json.dumps({
            "type": "call_incoming",
            "from_id": event["from_id"],
            "from_name": event["from_name"]
        }))



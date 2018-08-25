import asyncio
import sys

import telepot
from app_secrets import TELEGRAM_API_TOKEN as TOKEN
from entree_sortie import FICHIER_EMAILS_CHEMIN, supprimer_email
from telepot.aio.delegate import create_open, pave_event_space, per_chat_id
from telepot.aio.loop import MessageLoop


class MessageCounter(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageCounter, self).__init__(*args, **kwargs)

    async def on_chat_message(self, msg):
        print("message reçu:")
        if "text" in msg.keys():
            print(msg["text"])
            if msg["text"] == "/emails":
                with open(FICHIER_EMAILS_CHEMIN, "r") as docFile:
                    print("Sending document")
                    await self.sender.sendDocument(document=docFile)
            elif "/unsubscribe" in msg["text"]:
                email = msg["text"].split(" ")
                if len(email) > 1:
                    email = email[1]
                    result = supprimer_email(email)
                    if result:
                        await self.sender.sendMessage("Email supprimé avec succès.")
                    else:
                        await self.sender.sendMessage("Email non trouvé, email non supprimé.")
                else:
                    await self.sender.sendMessage("Il faut fournir un email pour désinscrire un abonné.")


bot = telepot.aio.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, MessageCounter, timeout=10),
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Listening ...')

loop.run_forever()

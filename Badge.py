#!/usr/bin/env python3
# Version modifiee de la librairie https://github.com/mxgxw/MFRC522-python
import signal
from time import sleep

import modules.MFRC522 as MFRC522
from modules.entree_sortie import (FICHIER_DERNIER_BADGE_SCANNE_CHEMIN,
                                   ajouter_entree, rechercher_rfid)
from pyA20.gpio import gpio

gpio.init()  # Initialize module. Always called first

continue_reading = True


def end_read(signal, frame):
    """Fonction qui arrete la lecture proprement."""
    global continue_reading
    print ("Lecture terminée")
    continue_reading = False
    gpio.cleanup()


print("init")
signal.signal(signal.SIGINT, end_read)
MIFAREReader = MFRC522.MFRC522()

print ("Passer le tag RFID a lire")

while continue_reading:
    # Detecter les tags
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    # Une carte est detectee
    if status == MIFAREReader.MI_OK:
        print ("Carte detectee")
    # Recuperation UID
    (status, uid) = MIFAREReader.MFRC522_Anticoll()
    if status == MIFAREReader.MI_OK:
        # Clee d authentification par defaut
        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        # Selection du tag
        MIFAREReader.MFRC522_SelectTag(uid)
        # Authentification
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
        code = str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])
        nom, prenom, dateAdhesion = rechercher_rfid(code)
        ajouter_entree(nom, prenom, dateAdhesion)

        if not dateAdhesion:
            with open(FICHIER_DERNIER_BADGE_SCANNE_CHEMIN, 'w') as no_adhe:
                no_adhe.write(code)
                print("carte non repertioriee")

        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print ("Erreur d'Authentification")

        sleep(.2)

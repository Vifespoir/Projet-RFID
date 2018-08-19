#!/usr/bin/env python3
# Version modifiee de la librairie https://github.com/mxgxw/MFRC522-python
import signal
from time import sleep, time

import modules.MFRC522 as MFRC522
from modules.entree_sortie import (FICHIER_DERNIER_BADGE_SCANNE_CHEMIN,
                                   FICHIER_DES_ENTREES_CHEMIN, ajouter_entree,
                                   rechercher_rfid)
from pyA20.gpio import gpio
from redis import StrictRedis


class BadgeScanneur(object):
    """docstring for BadgeScanneur."""
    def __init__(self):
        super(BadgeScanneur, self).__init__()
        self.redis = StrictRedis(host='localhost', port=6379, db=0)
        gpio.init()  # Initialize module. Always called first
        self.continue_reading = True
        signal.signal(signal.SIGINT, self.end_read)
        self.MIFAREReader = MFRC522.MFRC522()
        self.redis.publish("stream", "<success>Badgeuse initialisé, prête à scanner.")

    def end_read(self, signal, frame):
        """Fonction qui arrete la lecture proprement."""
        self.redis.publish("stream", "<warning>Lecture terminée, badgeuse arrêtée.")
        self.continue_reading = False
        gpio.cleanup()

    def rechercher_adherent(self, code):
        result = rechercher_rfid(code)
        if result:
            return result
        else:
            return (None, None, None)

    def authentifier_rfid(self, nom, prenom, dateAdhesion):
        ajouter_entree(nom, prenom, dateAdhesion)

    def main(self):
        lastCode = (None, time())
        dejaScanne = None
        while self.continue_reading:
            # Detecter les tags
            (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
            # Recuperation UID
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            if status == self.MIFAREReader.MI_OK:
                # Clee d authentification par defaut
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                # Selection du tag
                self.MIFAREReader.MFRC522_SelectTag(uid)
                # Authentification
                status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
                code = str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])
                with open(FICHIER_DES_ENTREES_CHEMIN, 'r') as fichierEntrees:
                    lignes = fichierEntrees.readlines()
                    ligne = lignes[-1]

                nom, prenom, dateAdhesion = self.rechercher_adherent(code)
                if (code != lastCode[0] or (time() - lastCode[1] > 1000*60*60*2)) and nom not in ligne:
                    lastCode = (code, time())
                    self.authentifier_rfid(nom, prenom, dateAdhesion)
                    self.redis.publish("stream",
                                       "<warning>Bonjour, {}! Bons projets!".format(prenom))
                elif nom is None:
                    with open(FICHIER_DERNIER_BADGE_SCANNE_CHEMIN, 'w') as no_adhe:
                        # FIXME delete this file
                        no_adhe.write(code)
                        self.redis.publish("stream",
                                           "<danger>Badge non repertorié: {}, voulez-vous l'associer?"
                                           .format(code))
                else:
                    if dejaScanne and time() - dejaScanne < 10:
                        continue
                    dejaScanne = time()
                    self.redis.publish("stream",
                                       "<warning>Bien tenté {} mais ton badge est déjà scanné! {}"
                                       .format(prenom))
                    else:
                        nom, prenom = self.authentifier_rfid(code)

                self.MIFAREReader.MFRC522_StopCrypto1()
            else:
                # DEBUG POUR DEBUGGER SEULEMENT
                # self.redis.publish("danger", "Erreur d'Authentification")
                pass

            sleep(.2)


if __name__ == '__main__':
    badgeScanneur = BadgeScanneur()
    badgeScanneur.main()

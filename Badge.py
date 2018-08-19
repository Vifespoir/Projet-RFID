#!/usr/bin/env python3
# Version modifiee de la librairie https://github.com/mxgxw/MFRC522-python
import signal
from time import sleep

import modules.MFRC522 as MFRC522
from modules.entree_sortie import (FICHIER_DERNIER_BADGE_SCANNE_CHEMIN,
                                   ajouter_entree, rechercher_rfid)
from pyA20.gpio import gpio
from redis import StrictRedis


class BadgeScanneur(object):
    """docstring for BadgeScanneur."""
    def __init__(self):
        super(BadgeScanneur, self).__init__()
        print("init")
        self.redis = StrictRedis(host='localhost', port=6379, db=0)
        gpio.init()  # Initialize module. Always called first
        self.continue_reading = True
        signal.signal(signal.SIGINT, self.end_read)
        self.MIFAREReader = MFRC522.MFRC522()
        print ("Passer le tag RFID a lire")

    def end_read(self, signal, frame):
        """Fonction qui arrete la lecture proprement."""
        print ("Lecture terminée")
        self.continue_reading = False
        gpio.cleanup()

    def authentifier_rfid(self, code):
        result = rechercher_rfid(code)
        if result:
            nom, prenom, dateAdhesion = result
            ajouter_entree(nom, prenom, dateAdhesion)
        else:
            with open(FICHIER_DERNIER_BADGE_SCANNE_CHEMIN, 'w') as no_adhe:
                no_adhe.write(code)
                print("carte non repertioriee")

    def main(self):
        lastCode = None
        while self.continue_reading:
            # Detecter les tags
            (status, TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
            # Une carte est detectee
            if status == self.MIFAREReader.MI_OK:
                self.redis.publish("stream", "Carte detectée")
            # Recuperation UID
            (status, uid) = self.MIFAREReader.MFRC522_Anticoll()
            if status == self.MIFAREReader.MI_OK:
                self.redis.publish("stream", "Badge scanné")
                # Clee d authentification par defaut
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
                # Selection du tag
                self.MIFAREReader.MFRC522_SelectTag(uid)
                # Authentification
                status = self.MIFAREReader.MFRC522_Auth(self.MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
                code = str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3])
                if code != lastCode:
                    lastCode = code
                    self.authentifier_rfid(code)

                self.MIFAREReader.MFRC522_StopCrypto1()
            else:
                self.redis.publish("stream", "Erreur d'Authentification")

                sleep(.2)


if __name__ == '__main__':
    badgeScanneur = BadgeScanneur()
    badgeScanneur.main()

#!/usr/bin/env python
# -*- coding: utf8 -*-
# Version modifiee de la librairie https://github.com/mxgxw/MFRC522-python

import signal

# import RPi.GPIO as GPIO
import MFRC522
from pyA20.gpio import gpio

continue_reading = True

gpio.init()
MIFAREReader = MFRC522.MFRC522()


def end_read(signal, frame):
    """Fonction qui arrete la lecture proprement."""
    global continue_reading
    print ("Lecture terminée")
    continue_reading = False
    gpio.cleanup()


signal.signal(signal.SIGINT, end_read)

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
        print ("UID de la carte : "+str(uid[0])+"."+str(uid[1])+"."+str(uid[2])+"."+str(uid[3]))

        # Clee d authentification par defaut
        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

        # Selection du tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authentification
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_Read(8)
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print ("Erreur d\'Authentification")

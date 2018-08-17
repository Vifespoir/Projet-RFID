#!/usr/bin/env python3
# Version modifiee de la librairie https://github.com/mxgxw/MFRC522-python
import signal
from datetime import strftime, strptime
from time import sleep

import MFRC522
from pyA20.gpio import gpio

gpio.init()  # Initialize module. Always called first


fichier = '/home/michel/Documents/test.csv'
sortie = '/home/michel/Documents/sortie.txt'
no_adherent = '/home/michel/Documents/non_repertorie.txt'

continue_reading = True


def end_read(signal, frame):
    """Fonction qui arrete la lecture proprement."""
    global continue_reading
    print ("Lecture terminée")
    continue_reading = False
    gpio.cleanup()


def faire_string(ligne):
    ligne = line.split(',')
    date_cotisation = strptime(ligne[4], '%d/%m/%Y')
    date = date_cotisation.date()
    difference = date.today() - date
    if difference.days < 365:
        texte = ' Oui'
    else:
        texte = ' Date_de_cotisation_depassee'
    date = strftime("%A %d %B %Y %H:%M")

    return '\n' + date + ' ' + ligne[2] + ' ' + ligne[1] + texte


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

        compteur = 0
        for line in open(fichier):
            if code in line:
                compteur += 1
                test = open(sortie, 'a')
                entree = faire_string(line)
                test.write(entree)
                test.close()

        if compteur == 0:
            with open(no_adherent, 'w') as no_adhe:
                no_adhe.write(code)
                print("carte non repertioriee")

        if status == MIFAREReader.MI_OK:
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print ("Erreur d\'Authentification")

        sleep(3)

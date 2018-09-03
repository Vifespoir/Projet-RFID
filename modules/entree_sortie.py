#!/usr/bin/env python3
# -*- coding: utf_8 -*-
from csv import DictReader, DictWriter
from datetime import date, datetime
from os import remove, rename
from os.path import abspath, dirname, join, pardir
from re import compile as re_compile

DOSSIER_DONNEES = "data"
CHEMIN_DONNEES = abspath(join(dirname(__file__), pardir, DOSSIER_DONNEES))

CSV_ADHERENTS = "adherents.csv"
CHEMIN_CSV_ADHERENTS = join(CHEMIN_DONNEES, CSV_ADHERENTS)
CSV_ENTREES = "registre_des_entrees.txt"
CHEMIN_CSV_ENTREES = join(CHEMIN_DONNEES, CSV_ENTREES)
TXT_DERNIER_BADGE = "dernier_badge_scanne.txt"
CHEMIN_TXT_DERNIER_BADGE = join(CHEMIN_DONNEES, TXT_DERNIER_BADGE)
CSV_EMAILS = "emails.csv"
CHEMIN_CSV_EMAILS = join(CHEMIN_DONNEES, CSV_EMAILS)
# REGEXES
TEST_MME_MR = re_compile(r"([M.|Mme])")
TEST_NOM = re_compile(r"(\S+)")
TEST_EMAIL = re_compile(r"(\S+)(@)(\S+)")
TEST_DATE = re_compile(r"\d{2}\/\d{2}\/\d{4}")
TEST_RFID = re_compile(r"\d+")
# Paramètre de lecture pour obtenir les résultats sous forme de dictionnaire
CSV_DATE = "Date"
CSV_HEURE = "Heure"
CSV_PRENOM = "Prenom"
CSV_NOM = "Nom"
CSV_EMAIL = "E-mail"
CSV_COTISATION = "Date de cotisation"
CSV_STATUS = "Status cotisation"
CSV_RFID = "RFID"
CSV_GENRE = "Genre"
ENTETE_CSV_ADHERENTS = [CSV_GENRE, CSV_NOM, CSV_PRENOM, CSV_EMAIL, CSV_COTISATION, CSV_RFID]
SEPARATEUR_CSV_ADHERENTS = ","
PARAMETRE_CSV_ADHERENTS = {"fieldnames": ENTETE_CSV_ADHERENTS, "delimiter": SEPARATEUR_CSV_ADHERENTS}
ENTETE_REGISTRE_DES_ENTREES = [CSV_DATE, CSV_HEURE, CSV_PRENOM, CSV_NOM, CSV_STATUS]
SEPARATEUR_REGISTRE_DES_ENTREES = " "
PARAMETRE_CSV_REGISTRE_DES_ENTREES = {"fieldnames": ENTETE_REGISTRE_DES_ENTREES,
                                      "delimiter": SEPARATEUR_REGISTRE_DES_ENTREES}
ENTETE_CSV_EMAILS = [CSV_PRENOM, CSV_NOM, CSV_EMAIL]
SEPARATEUR_CSV_EMAILS = ","
PARAMETRE_CSV_EMAILS = {"fieldnames": ENTETE_CSV_EMAILS, "delimiter": SEPARATEUR_CSV_EMAILS}


def ecrire_fichier_csv(fichier, contenu, mode, parametres):
    with open(fichier, mode=mode, newline="") as fichierEmail:
        ecriture = DictWriter(fichierEmail, **parametres)
        ecriture.writerows(contenu)


def lire_fichier_csv(fichier, parametres):
    with open(fichier, mode="r", newline="") as fichierLu:
        csvLu = DictReader(fichierLu, **parametres)

        contenu = list(csvLu)

    return contenu


def ajouter_ligne_csv(ligneCsv):
    """Permet d'écrire dans la base de donnée csv."""
    assert isinstance(ligneCsv, list()), "Le contenu n'est pas une liste..."
    assert isinstance(ligneCsv[0], dict()), "La ligne n'est pas un dictionnaire..."
    ecrire_fichier_csv(CHEMIN_CSV_ADHERENTS, ligneCsv, mode="a", parametres=PARAMETRE_CSV_ADHERENTS)


def formatter_ligne_csv(nom, prenom, dateAdhesion):
    """Permet d'écrire dans le fichier des entrées."""
    date, heure = obtenir_date_et_heure_actuelle()
    nouvelleLigne = {CSV_NOM: nom, CSV_PRENOM: prenom, CSV_DATE: date, CSV_HEURE: heure}
    if dateAdhesion:
        date = datetime.strptime(dateAdhesion, '%d/%m/%Y')
        difference = datetime.today() - date
        if difference.days < 365:
            nouvelleLigne[CSV_STATUS] = 'Oui'
        else:
            nouvelleLigne[CSV_STATUS] = 'Date_de_cotisation_depassee'
    else:
        nouvelleLigne[CSV_STATUS] = 'Visiteur'

    return nouvelleLigne


def obtenir_date_et_heure_actuelle():
    maintenant = datetime.today()
    heure = maintenant.strftime("%H:%M")
    date = str(maintenant.date())
    return date, heure


def supprimer_ligne_du_csv_adherent(ligneCsv):
    """Supprime une ligne donnée du fichier adhérent."""
    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)

    for ligne in csvLu:
        if ligneCsv == ligne:
            print("Supression de la ligne: {}".format(ligne))
            csvLu.remove(ligne)
            break

    ecrire_fichier_csv(CSV_ADHERENTS, csvLu, mode="w", parametres=PARAMETRE_CSV_ADHERENTS)


def lire_dernier():
    """Permet de lire le dernier badge non repertorié qui a été badgé."""
    with open(CHEMIN_TXT_DERNIER_BADGE, mode='r') as fichierBadge:
        contenu = fichierBadge.read()

    return contenu.strip()


def supprimer_rfid_adherent(numero):
    """Ouvre le fichier adherent pour y chercher une cle et la supprimer."""
    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)

    for ligne in csvLu:
        if ligne[CSV_RFID] == numero:
            ligne[CSV_RFID] = ""
            texte = "Vous avez supprimé l'ID de l'adhérent : " + ligne[CSV_NOM] + " " + ligne[CSV_PRENOM]
            break
    else:
        texte = "Pas d'adhérent associé à cet ID"

    ecrire_fichier_csv(CHEMIN_CSV_ADHERENTS, csvLu, mode="w", parametres=PARAMETRE_CSV_ADHERENTS)

    return texte


def ajouter_rfid_adherent(nom, prenom, numero):
    """Associe un adhérent à un ID rfid."""
    if rechercher_rfid(numero):
        return "Numéro RFID déjà associer, merci de bien vouloir rapporter le bug."

    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)
    for ligne in csvLu:
        if ligne[CSV_NOM].lower() == nom.lower() and ligne[CSV_PRENOM].lower() == prenom.lower():
            ligne[CSV_RFID] = numero
            texte = "Vous avez associé l'adhérent {} {} au numéro {}".format(
                ligne[CSV_PRENOM], ligne[CSV_NOM], ligne[CSV_RFID])
            break

    ecrire_fichier_csv(CHEMIN_CSV_ADHERENTS, csvLu, mode="w", parametres=PARAMETRE_CSV_ADHERENTS)

    return texte


def rechercher_adherent(nom, uri):
    """Recherche un adherent et l'associe."""
    lignes = []
    texte = "Voici la liste des adhérents comportant : " + nom

    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)

    for ligne in csvLu:
        baseNom = ligne[CSV_NOM] + " " + ligne[CSV_PRENOM]
        if nom.lower() in baseNom.lower():
            ligne["uri"] = ""
            lignes.append(ligne)

    if not lignes:
        texte = "Pas d'adhérent au nom de : {}".format(nom)

    return texte, lignes


def rechercher_date_adhesion(nom, prenom):
    dateAdhesion = None
    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)
    for ligne in csvLu:
        if nom == ligne[CSV_NOM] and prenom == ligne[CSV_PRENOM]:
            dateAdhesion = ligne[CSV_COTISATION]

    return dateAdhesion


def ajouter_entree(nom, prenom, dateAdhesion):
    entree = [formatter_ligne_csv(nom, prenom, dateAdhesion)]
    ecrire_fichier_csv(CHEMIN_CSV_ENTREES, entree, mode="a", parametres=PARAMETRE_CSV_REGISTRE_DES_ENTREES)


def rechercher_entrees(nom=None, prenom=None, jour=None):
    entrees = []
    if nom is None and prenom is None and jour is None:
        raise UserWarning("Aucune clé n'a été fourni pour la recherche...")

    csvLu = lire_fichier_csv(CHEMIN_CSV_ENTREES, parametres=PARAMETRE_CSV_REGISTRE_DES_ENTREES)
    for ligne in csvLu:
        if prenom and nom:
            print(ligne)
            if nom == ligne[CSV_NOM] and prenom == ligne[CSV_PRENOM]:
                print("NAME")
                entrees.append(ligne)
            else:
                print("NO NAME")
        else:
            if jour in ligne[CSV_DATE]:
                entrees.append(ligne)

    print(entrees)

    return entrees


def lire_entrees_du_jour():
    jour = str(date.today())
    entrees = rechercher_entrees(jour=jour)
    return entrees


def rechercher_rfid(numero):
    csvLu = lire_fichier_csv(CHEMIN_CSV_ADHERENTS, parametres=PARAMETRE_CSV_ADHERENTS)
    for ligne in csvLu:
        if numero in ligne:
            return ligne[CSV_NOM], ligne[CSV_PRENOM], ligne[CSV_COTISATION]
    else:
        return None


def test_fichier_csv(fichier):
    """Function to test that the uploaded csv matches the specs.

    Exemple de ligne: "M.,BÉLIÈRES,Denis,denibel@yahoo.fr,25/03/2018,19253157164"
    """
    csvLu = lire_fichier_csv(fichier, parametres=PARAMETRE_CSV_ADHERENTS)
    compteur = 1
    for ligne in csvLu[1:]:  # ignore la première ligne du fichier csv
        compteur += 1
        try:
            assert TEST_MME_MR.match(ligne[CSV_GENRE]), "Problem with prefix :" + ligne[CSV_GENRE]
            assert TEST_NOM.match(ligne[CSV_PRENOM]), "Problem with 1st name :" + ligne[CSV_PRENOM]
            assert TEST_NOM.match(ligne[CSV_NOM]), "Problem with last name :" + ligne[CSV_NOM]
            if ligne[CSV_EMAIL]:
                assert TEST_EMAIL.match(ligne[CSV_EMAIL]), "Problem with email :" + ligne[CSV_EMAIL]
            else:
                print("ERREUR SUR LA LIGNE: {}".format(ligne))
            assert TEST_DATE.match(ligne[CSV_COTISATION]), "Problem with date :" + ligne[CSV_COTISATION]
            if ligne[CSV_RFID]:
                assert TEST_RFID.match(ligne[CSV_RFID]), "Problem with RFID :" + ligne[CSV_RFID]
            else:
                print("ERREUR NO RFID")
        except AssertionError as e:
            print(e)
            return "Erreur ligne: {}\n{}\n{}".format(compteur, ", ".join(ligne), e)
    else:
        return True


def reecrire_registre_des_entrees(fichier):
    archive = "{}-{}.csv".format(CHEMIN_CSV_ADHERENTS[:-4] + str(datetime.today()))
    rename(CHEMIN_CSV_ADHERENTS, archive)

    csvLu = lire_fichier_csv(fichier, parametres=PARAMETRE_CSV_ADHERENTS)

    ecrire_fichier_csv(CHEMIN_CSV_ADHERENTS, csvLu, mode="w", parametres=PARAMETRE_CSV_ADHERENTS)

    remove(fichier)


def ajouter_email(nom, prenom, email):
    nouvelleLigne = [{CSV_NOM: nom, CSV_PRENOM: prenom, CSV_EMAIL: email}]
    ecrire_fichier_csv(CHEMIN_CSV_EMAILS, nouvelleLigne, mode="a", parametres=PARAMETRE_CSV_EMAILS)


def supprimer_email(email):
    csvLu = lire_fichier_csv(CHEMIN_CSV_EMAILS, parametres=PARAMETRE_CSV_EMAILS)
    nombreEmails = len(csvLu)
    for ligne in csvLu:
        if ligne and email.lower() in ligne[CSV_EMAIL].lower():
            csvLu.remove(ligne)
            break

    if nombreEmails == len(csvLu):
        return False

    ecrire_fichier_csv(CHEMIN_CSV_EMAILS, csvLu, mode="w", parametres=PARAMETRE_CSV_EMAILS)
    return True

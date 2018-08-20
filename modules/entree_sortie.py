#!/usr/bin/env python3
# -*- coding: utf_8 -*-
from csv import reader, writer
from datetime import datetime
from os.path import abspath, dirname, isdir, join, pardir

DOSSIER_DONNEES = "data"
CHEMIN_DONNEES = abspath(join(dirname(__file__), pardir, DOSSIER_DONNEES))
if not isdir(CHEMIN_DONNEES):
    DOSSIER_DONNEES = "data-test"
    CHEMIN_DONNEES = abspath(join(dirname(__file__), pardir, DOSSIER_DONNEES))

FICHIER_ADHERENTS = "adherents.csv"
FICHIER_ADHERENTS_CHEMIN = join(CHEMIN_DONNEES, FICHIER_ADHERENTS)
FICHIER_DES_ENTREES = "registre_des_entrees.txt"
FICHIER_DES_ENTREES_CHEMIN = join(CHEMIN_DONNEES, FICHIER_DES_ENTREES)
FICHIER_DERNIER_BADGE_SCANNE = "dernier_badge_scanne.txt"
FICHIER_DERNIER_BADGE_SCANNE_CHEMIN = join(CHEMIN_DONNEES, FICHIER_DERNIER_BADGE_SCANNE)


def ajouter_ligne_csv(ligneCsv):
    """Permet d'écrire dans la base de donnée csv."""
    with open(FICHIER_ADHERENTS_CHEMIN, 'a') as ecriture:
        scribeCsv = writer(ecriture)
        scribeCsv.writerow(ligneCsv)


def formatter_ligne_csv(nom, prenom, dateAdhesion):
    """Permet d'écrire dans le fichier des entrées."""
    if dateAdhesion:
        date = datetime.strptime(dateAdhesion, '%d/%m/%Y')
        difference = datetime.today() - date
        if difference.days < 365:
            texte = 'Oui'
        else:
            texte = 'Date_de_cotisation_depassee'
    else:
        texte = 'Visiteur'
    maintenant = datetime.today()
    heure = maintenant.strftime("%H:%M")
    maintenant = str(maintenant.date())

    return "\n{} {} {} {} {}".format(maintenant, heure, prenom, nom, texte)


def supprimer_ligne_du_csv_adherent(ligneCsv):
    """Supprime une ligne donnée du fichier adhérent."""
    contenu = []
    print("deleting")
    with open(FICHIER_ADHERENTS_CHEMIN, "r") as fichierOriginal:
        lignes = reader(fichierOriginal)
        for ligne in lignes:
            if not(ligneCsv == ligne):
                contenu.append(ligne)
            else:
                print("deleting")

    with open(FICHIER_ADHERENTS_CHEMIN, 'w') as nouveauFichier:
        ecrireCsv = writer(nouveauFichier)
        ecrireCsv.writerows(contenu)


def lire_dernier():
    """Permet de lire le dernier badge non repertorié qui a été badgé."""
    with open(FICHIER_DERNIER_BADGE_SCANNE_CHEMIN, 'r') as fichierBadge:
        contenu = fichierBadge.read()

    return contenu


def supprimer_rfid_adherent(numero):
    """Ouvre le fichier adherent pour y chercher une cle et la supprimer."""
    with open(FICHIER_ADHERENTS_CHEMIN, 'r') as fichierLu:
        liseuseCsv = reader(fichierLu)
        lignes = list(liseuseCsv)
        for ligne in lignes:
            nom = ligne[1]
            prenom = ligne[2]
            if ligne[5] == numero:
                ligne[5] = ""
                texte = "Vous avez supprimé l'ID de l'adhérent : " + nom + " " + prenom
                break
        else:
            texte = "Pas d'adhérent associé à ce ID"

    with open(FICHIER_ADHERENTS_CHEMIN, 'w') as fichierEcriture:
        ecrireCsv = writer(fichierEcriture)
        ecrireCsv.writerows(lignes)

    return texte


def ajouter_rfid_adherent(nom, prenom, numero):
    """Associe un adhérent à un ID rfid."""
    with open(FICHIER_ADHERENTS_CHEMIN, 'r') as fichier_read:
        liseuseCsv = reader(fichier_read)
        for ligne in liseuseCsv:
            if ligne[1].lower() == nom.lower() and ligne[2].lower() == prenom.lower():
                chaine = ligne[0:5]
                chaine.append(numero)
                texte = "Vous avez associé l'adhérent {} {} au numéro {}".format(ligne[2], ligne[1], numero)
                break

    supprimer_ligne_du_csv_adherent(ligne)
    ajouter_ligne_csv(chaine)
    return texte


def rechercher_adherent(nom, uri):
    """Recherche un adherent et l'associe."""
    lignes = []
    texte = "Voici la liste des adhérents comportant : " + nom

    for ligne in open(FICHIER_ADHERENTS_CHEMIN, "r"):
        ligne = ligne.split(',')
        baseNom = ", ".join(ligne[1:3])
        if nom.lower() in baseNom.lower():
            # line[1]: Nom line[2]:Prénom line[5]:numero badge
            nouvelleUri = uri.format(ligne[1], ligne[2])
            nouvelleLigne = [ligne[2], ligne[1], nouvelleUri]
            lignes.append(nouvelleLigne)

    if not lignes:
        texte = "Pas d'adhérent au nom de : {}".format(nom)

    return texte, lignes


def rechercher_date_adhesion(nom, prenom):
    dateAdhesion = None
    with open(FICHIER_ADHERENTS_CHEMIN, "r") as fichierAdherents:
        lignes = fichierAdherents.readlines()
        for ligne in lignes:
            ligne = ligne.split(",")
            if nom in ligne and prenom in ligne:
                dateAdhesion = ligne[4]

    return dateAdhesion


def ajouter_entree(nom, prenom, dateAdhesion):
    with open(FICHIER_DES_ENTREES_CHEMIN, 'a') as fichierEntrees:
        entree = formatter_ligne_csv(nom, prenom, dateAdhesion)
        fichierEntrees.write(entree)


def rechercher_entrees(nom, prenom):
    entrees = []
    with open(FICHIER_DES_ENTREES_CHEMIN, "r") as fichierEntrees:
        lignes = fichierEntrees.readlines()
        for ligne in lignes:
            if prenom in ligne and nom in ligne:
                ligne = ligne.split(' ')
                entrees.extend(ligne[0:5])

    return entrees


def rechercher_rfid(numero):
    with open(FICHIER_ADHERENTS_CHEMIN, "r") as fichierAdherents:
        adherents = reader(fichierAdherents)
        for ligne in adherents:
            if numero in ligne:
                return ligne[1], ligne[2], ligne[4]  # nom prenom date_adhesion
        else:
            return None

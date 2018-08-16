#!/usr/bin/env python
# -*- coding: utf_8 -*-
import csv
import os
from datetime import date, datetime, strftime, timedelta

from flask import Flask, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_security import (RoleMixin, Security, SQLAlchemyUserDatastore,
                            UserMixin, login_required)
from flask_sqlalchemy import SQLAlchemy

# from os import getcwd


fichier_adherent = '/home/michel/Documents/test.csv'
fichier_temp = '/home/michel/Documents/fichier_temporaire.csv'
vrai_fichier_adherent = '/home/michel/Documents/UTF-8.csv'
sortie = '/home/michel/Documents/sortie.txt'
dernier_badge = '/home/michel/Documents/non_repertorie.txt'
accueil = "/"
historique = "/historique"
admin = "/admin"
login = '/login'
logout = '/logout'
visiteur = '/visiteur'


def ecrire(chaine):
    """Permet d'écrire dans la base de donnée csv."""
    with open(fichier_temp, 'a') as ecriture:
        test = csv.writer(ecriture)
        test.writerow(chaine)


def faire_string(line):
    """Permet d'écrire dans le fichier des entrées."""
    ligne = line.split(',')
    date_cotisation = datetime.strptime(ligne[4], '%d/%m/%Y')
    date = date_cotisation.date()
    difference = date.today() - date
    if difference.days < 365:
        texte = ' Oui'
    else:
        texte = ' Date_de_cotisation_depassee'
    date1 = date.today()
    heure = strftime("%H:%M")
    date = str(date1)
    return '\n' + date + ' ' + heure + ' ' + ligne[2] + ' ' + ligne[1] + texte


def supprimer_ligne(chaine):
    contenu = ""

    fichier_supprimer = open(fichier_adherent, "r")
    for ligne in fichier_supprimer:
        if not(chaine in ligne):
            contenu += ligne
    fichier_supprimer.close()

    fichier_ecrire = open(fichier_adherent, 'w')
    fichier_ecrire.write(contenu)
    fichier_ecrire.close()


def lire_dernier():
    """Permet de lire le dernier badge non repertorié qui a été badgé."""
    fichier_lire = open(dernier_badge, 'r')
    contenu = fichier_lire.read()
    fichier_lire.close()
    return contenu


# Ne pas ajouter d'extensions au dessus
app = Flask(__name__)
# Extensions:
Bootstrap(app)
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECURITY_PASSWORD_SALT'] = 'zedzoedajdpaok'
app.config['SECURITY_POST_LOGIN_VIEW'] = admin
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login_user.html'


# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
security.SECURITY_PASSWORD_HASH = None


@app.before_first_request
def create_user():
    """Create a user to test with."""
    db.create_all()
    user_datastore.create_user(email='hatlab', password='hatlab')
    db.session.commit()


@app.route('/')
def retourner_accueil():
    contenu = []
    jour = str(date.today())
    for line in open(sortie):
        if jour in line:
            ligne = line.split(' ')
            heure = ligne[1]
            prenom = ligne[2]
            nom = ligne[3]
            cotisation = ligne[4]

            contenu.append(heure)
            contenu.append(prenom)
            contenu.append(nom)
            contenu.append(cotisation)

    return render_template('accueil.html',
                           visiteur=visiteur,
                           accueil=accueil,
                           historique=historique,
                           contenu=contenu,
                           jour=jour,
                           admin=admin,
                           logout=logout)


@app.route('/historique', methods=['GET', 'POST'])
def retourner_historique():
    if request.method == 'POST':
        if request.form['bouton'] == "rechercher":
            contenu = []
            jour = request.form['jour']
            mois = request.form['mois']
            annee = request.form['annee']
            date = annee + '-' + mois + '-' + jour
            suivant = '/changer?date='+date+'&temps=1'
            precedent = '/changer?date='+date+'&temps=-1'
            for line in open(sortie):
                if date in line:
                    ligne = line.split(' ')
                    date = ligne[0]
                    heure = ligne[1]
                    prenom = ligne[2]
                    nom = ligne[3]

                    contenu.append(date)
                    contenu.append(heure)
                    contenu.append(prenom)
                    contenu.append(nom)

        return render_template('voir_historique.html',
                               precedent=precedent,
                               suivant=suivant,
                               accueil=accueil,
                               historique=historique,
                               visiteur=visiteur,
                               admin=admin,
                               logout=logout,
                               date=date,
                               contenu=contenu)

    else:
        return render_template('historique.html',
                               visiteur=visiteur,
                               accueil=accueil,
                               historique=historique,
                               admin=admin,
                               logout=logout)


@app.route('/changer', methods=['GET', 'POST'])
def changer_date():
    contenu = []
    date = request.args.get('date')
    temps = request.args.get('temps')
    temps = int(temps)
    temp_date = datetime.strptime(date, '%Y-%m-%d')
    temp_date = temp_date.date()
    jour1 = timedelta(days=temps)
    jour_suivant = temp_date + jour1
    date = str(jour_suivant)
    suivant = '/changer?date=' + date + '&temps=1'
    precedent = '/changer?date=' + date + '&temps=-1'

    for line in open(sortie):
        if date in line:
            ligne = line.split(' ')
            date = ligne[0]
            heure = ligne[1]
            prenom = ligne[2]
            nom = ligne[3]
            contenu.append(date)
            contenu.append(heure)
            contenu.append(prenom)
            contenu.append(nom)

    return render_template('voir_historique.html',
                           precedent=precedent,
                           suivant=suivant,
                           accueil=accueil,
                           historique=historique,
                           visiteur=visiteur,
                           admin=admin,
                           logout=logout,
                           date=date,
                           contenu=contenu)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def retourner_admin():
    dernier = lire_dernier()
    texte = 'Espace Admin'
    if request.method == 'POST':

        if request.form['bouton'] == "supprimer":
            compteur = 0
            numero = request.form['numero']
            with open(fichier_adherent, 'r') as fichier_read:
                reader = csv.reader(fichier_read)
                for line in reader:
                    nom = line[1]
                    prenom = line[2]
                    chaine = [line[0], line[1], line[2], line[3], line[4], line[5]]
                    if line[5] == numero:
                        chaine = [line[0], line[1], line[2], line[3], line[4], ""]
                        compteur += 1
                        texte = "Vous avez supprimé l'ID de l'adhérent : " + nom + " " + prenom
                    ecrire(chaine)
                    if compteur == 0:
                        texte = "Pas d'adhérent associé à ce ID"

            os.rename('/home/michel/Documents/fichier_temporaire.csv', '/home/michel/Documents/test.csv')
            return render_template('confirmation.html',
                                   visiteur=visiteur,
                                   dernier=dernier,
                                   accueil=accueil,
                                   historique=historique,
                                   admin=admin,
                                   texte=texte,
                                   logout=logout)

        if request.form['bouton'] == "rechercher":

            contenu = []
            compteur = 0
            nom = request.form['nom']
            nom = nom.lower()
            texte = "Voici la liste des adhérents comportant : " + nom
            for ligne in open(vrai_fichier_adherent):
                line = ligne.split(',')
                nom_base = line[1] + ',' + line[2]

                minuscule = nom_base.lower()
                if nom in minuscule:
                    # line[1]: Nom line[2]:Prénom line[5]:numero badge
                    compteur += 1
                    url = '/ajouter?nom='+line[1]+'&prenom='+line[2]+'&numero='+dernier
                    liigne = [line[2], line[1], line[5], url]
                    contenu.append(liigne)

            if compteur == 0:
                texte = "Pas d'adhérent au nom de : " + nom
            return render_template('voir_adherents.html',
                                   visiteur=visiteur,
                                   dernier=dernier,
                                   texte=texte,
                                   nom=nom,
                                   accueil=accueil,
                                   historique=historique,
                                   admin=admin,
                                   contenu=contenu,
                                   logout=logout)

    else:
        return render_template('admin.html',
                               texte=texte,
                               visiteur=visiteur,
                               accueil=accueil,
                               historique=historique,
                               admin=admin,
                               logout=logout,
                               dernier=dernier)


@app.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter():
    if request.args['action'] == "entree":
        contenu = []
        prenom = request.args.get('prenom')
        nom = request.args.get('nom')
        cherche = prenom + ' ' + nom
        print(cherche)
        for ligne in open(sortie):
            if cherche in ligne:
                line = ligne.split(' ')
                contenu.append(line[0])
                contenu.append(line[1])
                contenu.append(line[2])
                contenu.append(line[3])

        return render_template('voir_entrees.html',
                               accueil=accueil,
                               historique=historique,
                               admin=admin,
                               logout=logout,
                               visiteur=visiteur,
                               contenu=contenu,
                               cherche=cherche)

    dernier = lire_dernier()
    prenom = request.args.get('prenom')
    nom = request.args.get('nom')
    numero = request.args.get('numero')
    texte = ''
    with open(fichier_adherent, 'r') as fichier_read:
                reader = csv.reader(fichier_read)
                for line in reader:
                    chaine = [line[0], line[1], line[2], line[3], line[4], line[5]]
                    if line[1] == nom:
                        if line[2] == prenom:
                            chaine = [line[0], line[1], line[2], line[3], line[4], numero]
                            texte = "Vous avez associé l'adhérent " + line[2] + " " + line[1] + " au numéro " + numero
                    ecrire(chaine)

    os.rename('/home/michel/Documents/fichier_temporaire.csv', '/home/michel/Documents/test.csv')
    return redirect(url_for('retourner_admin'))


@app.route('/sans_badge', methods=['GET', 'POST'])
def sans_badge():

    prenom = request.args.get('prenom')
    nom = request.args.get('nom')
    cherche = nom + ',' + prenom
    for ligne in open(fichier_adherent):
        if cherche in ligne:
            with open(sortie, 'a') as simuler_badge:
                entree = faire_string(ligne)
                simuler_badge.write(entree)

    return redirect(url_for('retourner_accueil'))


@app.route('/visiteur', methods=['GET', 'POST'])
def pagevisiteur():
    dernier = lire_dernier()
    if request.method == 'POST':
        if request.form['bouton'] == "visiteur":
            prenom = request.form['prenom']
            nom = request.form['nom']
            date1 = date.today()
            heure = strftime("%H:%M")
            daate = str(date1)
            entree = '\n' + daate + ' ' + heure + ' ' + prenom + ' ' + nom + ' visiteur'
            with open(sortie, 'a') as ecrire_visiteur:
                ecrire_visiteur.write(entree)
            return redirect(url_for('retourner_accueil'))

        if request.form['bouton'] == "rechercher":
            contenu = []
            compteur = 0
            nom = request.form['nom']
            nom = nom.lower()
            texte = "Voici la liste des adhérents comportant : " + nom
            for ligne in open(vrai_fichier_adherent):
                line = ligne.split(',')
                nom_base = line[1] + ',' + line[2]
                minuscule = nom_base.lower()
                if nom in minuscule:
                    # line[1]: Nom line[2]:Prénom line[5]:numero badge
                    line = ligne.split(',')
                    compteur += 1
                    url = '/sans_badge?nom='+line[1]+'&prenom='+line[2]
                    liigne = [line[2], line[1], line[5], url]
                    contenu.append(liigne)

            if compteur == 0:
                texte = "Pas d'adhérent au nom de : " + nom

            return render_template('voir_liste.html',
                                   visiteur=visiteur,
                                   dernier=dernier,
                                   texte=texte,
                                   accueil=accueil,
                                   historique=historique,
                                   admin=admin,
                                   contenu=contenu,
                                   logout=logout)

    else:
        return render_template('visiteur.html',
                               visiteur=visiteur,
                               accueil=accueil,
                               historique=historique,
                               admin=admin,
                               logout=logout)

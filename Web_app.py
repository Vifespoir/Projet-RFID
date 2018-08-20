#!/usr/bin/env python3
# -*- coding: utf_8 -*-
from datetime import date, datetime, timedelta
from re import compile as re_compile

from flask import (Flask, Response, flash, redirect, render_template, request,
                   url_for)
from flask_bootstrap import Bootstrap
from flask_security import (RoleMixin, Security, SQLAlchemyUserDatastore,
                            UserMixin, login_required)
from flask_sqlalchemy import SQLAlchemy
from modules.entree_sortie import (FICHIER_DES_ENTREES_CHEMIN, ajouter_entree,
                                   ajouter_rfid_adherent, lire_dernier,
                                   rechercher_adherent, rechercher_date,
                                   rechercher_date_adhesion,
                                   rechercher_entrees, supprimer_rfid_adherent)
from redis import StrictRedis

# TODO add the new adherent signup page
# TODO add a page for subscribing to the newsletter
# TODO add a page to submit a bug report or a feature request
# TODO turn entree sortie into a class
# TODO add a page to update adherents

APP_ACCUEIL = "/"
APP_HISTORIQUE = "/historique"
APP_ADMIN = "/admin"
APP_LOGIN = '/login'
APP_LOGOUT = '/logout'
APP_VISITEUR = '/visiteur'

APP_PATHS = {
    "accueil": APP_ACCUEIL,
    "historique": APP_HISTORIQUE,
    "admin": APP_ADMIN,
    "login": APP_LOGIN,
    "logout": APP_LOGOUT,
    "visiteur": APP_VISITEUR
}

HTML_WRAPPER = [
    "primary",
    "secondary",
    "success",
    "danger",
    "warning",
    "info",
    "dark"
]
HTML_FLASH = '<div class="temp alert lead alert-{} .alert-dismissible" role="alert">{}</div>'
STREAM_TYPE = re_compile(r"<(\w+)>(.+)")
BOUTON_AJOUT_BADGE = '<a class="btn btn-primary " name="bouton" value="ajouter" href="{}" role="button">Associer</a>'

# Ne pas ajouter d'extensions au dessus
app = Flask(__name__)
# Extensions:
Bootstrap(app)
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECURITY_PASSWORD_SALT'] = 'zedzoedajdpaok'
app.config['SECURITY_POST_LOGIN_VIEW'] = APP_ADMIN
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login_user.html'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

redis = StrictRedis(host='localhost', port=6379, db=0)


def event_stream():
    pubsub = redis.pubsub()
    pubsub.subscribe("stream")
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        jsMessage = message["data"]
        if isinstance(jsMessage, int):
            continue
        message = message["data"].decode()
        match = STREAM_TYPE.match(message)
        type = match.group(1)
        jsMessage = match.group(2)
        if "non repertorié" in jsMessage:
            jsMessage += BOUTON_AJOUT_BADGE.format(APP_PATHS["admin"])
        jsMessage = HTML_FLASH.format(type, jsMessage)
        yield "data: {}\n\n".format(jsMessage)


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


# Ensure even the login form receives the APP_PATHS
@security.context_processor
def security_context_processor():
    return APP_PATHS


@app.route('/')
def retourner_accueil():
    """Affiche les entrées du jour sur la page d'accueil."""
    jour = str(date.today())

    entreesDuJour = rechercher_date(jour, heure=True)

    return render_template('accueil.html',
                           contenu=entreesDuJour,
                           jour=jour,
                           active="accueil",
                           **APP_PATHS)


@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/historique', methods=['GET', 'POST'])
def retourner_historique():
    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        print("histoire")
        jour = request.form['jour']
        mois = request.form['mois']
        annee = request.form['annee']
        date = "{}-{}-{}".format(annee, mois, jour)
        suivant = '/changer?date={}&delta=1'.format(date)
        precedent = '/changer?date={}&delta=-1'.format(date)
        entreesDuJour = rechercher_date(date)
        entreesDuJour = rechercher_date(date)
    else:
        precedent = suivant = entreesDuJour = None
        date = str(datetime.today().date())

    suivant = '/changer?date={}&delta=1'.format(date)
    precedent = '/changer?date={}&delta=-1'.format(date)

    return render_template('historique.html',
                           active="historique",
                           precedent=precedent,
                           suivant=suivant,
                           date=date,
                           contenu=entreesDuJour,
                           **APP_PATHS)


@app.route('/changer', methods=['GET', 'POST'])
def changer_date():
    date = request.args.get('date')
    delta = int(request.args.get('delta'))
    dateTemporaire = datetime.strptime(date, '%Y-%m-%d')
    dateTemporaire = dateTemporaire.date()
    jourActuel = timedelta(days=delta)
    jourSuivant = dateTemporaire + jourActuel
    date = str(jourSuivant)
    suivant = '/changer?date={}&delta=1'.format(date)
    precedent = '/changer?date={}&delta=-1'.format(date)

    entreesDuJour = rechercher_date(date)

    return render_template('historique.html',
                           active="historique",
                           precedent=precedent,
                           suivant=suivant,
                           date=date,
                           contenu=entreesDuJour,
                           **APP_PATHS)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def retourner_admin():
    texte = 'Espace Admin'
    dernier = lire_dernier()
    if request.method == 'POST' and request.form['bouton'] == "supprimer":
        numero = request.form['numero']
        texte = supprimer_rfid_adherent(numero)
        flash(texte)
        return render_template('admin.html',
                               active="admin",
                               **APP_PATHS)

    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        nom = request.form['nom']
        # FIXME ajouter for associer? what to do with associer endpoint
        uri = "/ajouter?nom={}&prenom={}"
        texte, lignes = rechercher_adherent(nom, uri)
        for ligne in lignes:
            ligne.insert(-1, dernier)
            ligne[-1] += "&numero={}".format(dernier)
            print(ligne)

        return render_template('voir_adherents.html',
                               dernier=dernier,
                               texte=texte,
                               nom=nom,
                               contenu=lignes,
                               **APP_PATHS)

    else:
        return render_template('admin.html',
                               active="admin",
                               **APP_PATHS)


@app.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter():
    if request.method == "GET":
        prenom = request.args.get('prenom')
        nom = request.args.get('nom')
        numero = request.args.get('numero')
        if "action" in request.args.keys() and request.args['action'] == "entree":
            cherche = "{} {}".format(prenom, nom)
            lignes = rechercher_entrees(nom, prenom)

            return render_template('voir_entrees.html',
                                   contenu=lignes,
                                   cherche=cherche,
                                   **APP_PATHS)

        else:
            ajouter_rfid_adherent(nom, prenom, numero)
            flash("Association entre rfid '{}' et adhérent '{} {}' réussie.".format(numero, prenom, nom))

            return redirect(url_for('retourner_admin'))


@app.route('/simuler', methods=['GET', 'POST'])
def simuler():
    if request.method == "GET" and request.args["nom"] and request.args["prenom"] and request.args["numero"]:
        prenom = request.args.get('prenom')
        nom = request.args.get('nom')
        # numero = request.args.get('numero')
        cherche = "{} {}".format(prenom, nom)

        dateAdhesion = rechercher_date_adhesion(nom, prenom)
        ajouter_entree(nom, prenom, dateAdhesion)
        entrees = rechercher_entrees(nom, prenom)

        return render_template('voir_entrees.html',
                               contenu=entrees,
                               cherche=cherche,
                               **APP_PATHS)

    return redirect(url_for('retourner_admin'))


@app.route('/sans_badge', methods=['GET', 'POST'])
def sans_badge():
    if request.method == "POST":
        prenom = request.args.get('prenom')
        nom = request.args.get('nom')
        ajouter_entree(nom, prenom)

    return redirect(url_for('retourner_accueil'))


@app.route('/visiteur', methods=['GET', 'POST'])
def pagevisiteur():
    dernier = lire_dernier()
    if request.method == 'POST' and request.form['bouton'] == "visiteur":
        prenom = request.form['prenom']
        nom = request.form['nom']
        maintenant = date.today()
        heure = maintenant.strftime("%H:%M")
        maintenant = str(maintenant)
        entree = "\n{} {} {} {} visiteur".format(maintenant, heure, prenom, nom)
        with open(FICHIER_DES_ENTREES_CHEMIN, 'a') as ecrireVisiteur:
            ecrireVisiteur.write(entree)
        return redirect(url_for('retourner_accueil'))

    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        nom = request.form['nom']
        uri = "/simuler?nom={}&prenom={}"
        texte, lignes = rechercher_adherent(nom, uri)
        for ligne in lignes:
            print(ligne)
            ligne[-1] += "&numero={}".format(dernier)
            ligne.insert(-1, dernier)

        return render_template('voir_liste.html',
                               dernier=dernier,
                               texte=texte,
                               contenu=lignes,
                               **APP_PATHS)

    else:
        return render_template('visiteur.html',
                               active="visiteur",
                               **APP_PATHS)


if __name__ == '__main__':
    app.run(host="0.0.0.0")

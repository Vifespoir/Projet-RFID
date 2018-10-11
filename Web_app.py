#!/usr/bin/env python3
# -*- coding: utf_8 -*-
import logging
from datetime import datetime, timedelta
from os import path
from re import compile as re_compile

from requests import get as get_url

from flask import (Flask, Response, flash, g, redirect, render_template,
                   request, url_for)
from flask_bootstrap import Bootstrap
from flask_security import (RoleMixin, Security, SQLAlchemyUserDatastore,
                            UserMixin, login_required)
from flask_sqlalchemy import SQLAlchemy
from markdown import markdown
from modules.app_secrets import (SECRET_KEY, SECURITY_PASSWORD_SALT,
                                 TELEGRAM_API_CHAT_ID, TELEGRAM_API_TOKEN)
from modules.entree_sortie import (CSV_ADHERENTS, CSV_BUGS, CSV_COTISATION,
                                   CSV_DATE, CSV_DESCRIPTION, CSV_EMAIL,
                                   CSV_EMAILS, CSV_ENTREES, CSV_ETAT,
                                   CSV_EVENEMENT, CSV_EVENEMENTS, CSV_GENRE,
                                   CSV_HEURE, CSV_NOM, CSV_ORGANISME, CSV_OUI,
                                   CSV_PARTICIPANTS, CSV_PRENOM, ajouter_bug,
                                   ajouter_email, ajouter_entree,
                                   ajouter_evenement, ajouter_rfid_adherent,
                                   detecter_deja_scanne, editer_evenement,
                                   lire_dernier, obtenir_bugs,
                                   obtenir_derniers_evenements,
                                   rechercher_adherent,
                                   rechercher_date_adhesion,
                                   rechercher_entrees,
                                   reecrire_registre_des_entrees,
                                   supprimer_rfid_adherent, test_fichier_csv,
                                   update_stats)
from redis import StrictRedis
from redis import exceptions as redisExceptions
from werkzeug.utils import secure_filename

logging.basicConfig(filename='Web_app.log', level=logging.DEBUG)

APP_ROOT = ""
APP_ACCUEIL = "accueil"
APP_HISTORIQUE = "historique"
APP_ADMIN = "admin"
APP_LOGIN = "login"
APP_LOGOUT = "logout"
APP_VISITEUR = "visiteur"
APP_BUG = "bug"
APP_NEWS = "newsletter"
APP_ADHESION = "adhesion"
APP_CHANGELOG = "changelog"
APP_EVENEMENT = "evenement"
APP_BUGS = "bugs"
APP_EMAIL = "etienne.pouget@outlook.com"
APP_STREAM = "stream"

WEB_SIMULER = "simuler"
WEB_ENVOYER = "envoyer"
WEB_SUPPRIMER = "supprimer"
WEB_ENTREE = "entree"
WEB_TELEVERSER = "televerser"
WEB_AJOUTER = "ajouter"
WEB_ACTION = "action"
WEB_DATA = "data"
WEB_ACTIVE = "active"
WEB_DERNIER = "dernier"
WEB_VISITEUR = "visiteur"
WEB_POST = "POST"
WEB_GET = "GET"
WEB_BOUTON = "bouton"
WEB_NUMERO = "numero"
WEB_TEXTE = "texte"
WEB_CONTENU = "contenu"
WEB_URI = "uri"
WEB_RECHERCHER = "rechercher"
WEB_JOUR = "jour"
WEB_MOIS = "mois"
WEB_ANNEE = "annee"
CHEMIN_CHANGELOG = "CHANGELOG.md"

APP_PATHS = {
    APP_ACCUEIL: "/" + APP_ACCUEIL,
    APP_HISTORIQUE: "/" + APP_HISTORIQUE,
    APP_ADMIN: "/" + APP_ADMIN,
    APP_LOGIN: "/" + APP_LOGIN,
    APP_LOGOUT: "/" + APP_LOGOUT,
    APP_VISITEUR: "/" + APP_VISITEUR,
    APP_BUG: "/" + APP_BUG,
    APP_NEWS: "/" + APP_NEWS,
    APP_ADHESION: "/" + APP_ADHESION,
    APP_CHANGELOG: "/" + APP_CHANGELOG,
    APP_EVENEMENT: "/" + APP_EVENEMENT,
    APP_BUGS: "/" + APP_BUGS,
    APP_ROOT: "/",
    APP_STREAM: "/" + APP_STREAM
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


TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_API_TOKEN)
TELEGRAM_API_MESSAGE_PAYLOAD = {"chat_id": TELEGRAM_API_CHAT_ID, "text": "HELLO FROM PYTHON"}
# Upload
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = set(["csv", "txt"])

# TODO:
# decouper if else en utilisant @app.route('/post/<int:post_id>')
# sortir db

# Ne pas ajouter d'extensions au dessus
app = Flask(__name__)
# Extensions:
Bootstrap(app)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
app.config["SECURITY_PASSWORD_SALT"] = SECURITY_PASSWORD_SALT
app.config["SECURITY_POST_LOGIN_VIEW"] = APP_ADMIN
app.config["SECURITY_LOGIN_USER_TEMPLATE"] = "login_user.html"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


redis = StrictRedis(host='localhost', port=6379, db=0)
try:
    redis.pubsub().subscribe(APP_STREAM)
    redis_status = True
except redisExceptions.ConnectionError:
    redis_status = False


def event_stream():
    pubsub = redis.pubsub()
    pubsub.subscribe(APP_STREAM)
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        logging.info("Nouvelle entrée: {}\n".format(message))
        jsMessage = message[WEB_DATA]
        if isinstance(jsMessage, int):
            continue
        message = message[WEB_DATA].decode()
        match = STREAM_TYPE.match(message)
        type = match.group(1)
        jsMessage = match.group(2)
        if "non repertorié" in jsMessage:
            jsMessage += BOUTON_AJOUT_BADGE.format(APP_PATHS[APP_ADMIN])
        jsMessage = HTML_FLASH.format(type, jsMessage)
        logging.info("Output message: {}".format(jsMessage))
        yield "{}: {}\n\n".format(WEB_DATA, jsMessage)


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


# Setup stats
def flask_update_stats():
    g.visiteurCeJour, g.visiteurCetteSemaine, g.visiteurCeMois = update_stats()


app.before_request(flask_update_stats)


@app.before_first_request
def create_user():
    """Create a user to test with."""
    db.create_all()
    user_datastore.create_user(email="hatlab", password="hatlab")
    db.session.commit()


# Ensure even the login form receives the APP_PATHS
@security.context_processor
def security_context_processor():
    return APP_PATHS


@app.route(APP_PATHS[APP_ROOT])
def redirgiger_accueil():
    logging.info("Redirection à la racine: '/'")
    return redirect(url_for("retourner_accueil"))


@app.route(APP_PATHS[APP_STREAM])
def stream():
    if redis_status:
        return Response(event_stream(), mimetype="text/event-stream")
    else:
        return Response(None, mimetype="text/event-stream")


@app.route(APP_PATHS[APP_ACCUEIL], methods=[WEB_POST, WEB_GET])
def retourner_accueil():
    """Affiche les entrées du jour sur la page d'accueil."""
    logging.info("Page de {}".format(APP_ACCUEIL))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))
    dernier = lire_dernier()
    kwargs = {WEB_ACTIVE: WEB_VISITEUR, WEB_DERNIER: dernier}
    if request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_VISITEUR:
        ligneCsv = {CSV_PRENOM: request.form[CSV_PRENOM], CSV_NOM: request.form[CSV_NOM],
                    CSV_EMAIL: request.form[CSV_EMAIL], CSV_ORGANISME: request.form[CSV_ORGANISME]}
        logging.info("Visiteur: {}".format(ligneCsv))
        if ligneCsv[CSV_EMAIL]:
            ajouter_email(ligneCsv[CSV_NOM], ligneCsv[CSV_PRENOM], ligneCsv[CSV_EMAIL])

        if not detecter_deja_scanne(ligneCsv[CSV_NOM], ligneCsv[CSV_PRENOM]):
            ajouter_entree(ligneCsv[CSV_NOM], ligneCsv[CSV_PRENOM], WEB_VISITEUR)
            flash("Bonjour, {}! Bons projets!".format(ligneCsv[CSV_PRENOM]))
        else:
            flash("Bien tenté {} mais tu t'es déjà inscrit!".format(ligneCsv[CSV_PRENOM]))

        return redirect(url_for("retourner_accueil"))

    if request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_RECHERCHER:
        kwargs[CSV_NOM] = request.form[CSV_NOM]
        uri = "/simuler?{CSV_NOM}={nom}&{CSV_PRENOM}={prenom}&{WEB_NUMERO}={numero}"
        kwargs[WEB_TEXTE], kwargs[WEB_CONTENU] = rechercher_adherent(kwargs[CSV_NOM], uri)
        for ligne in kwargs[WEB_CONTENU]:
            ligne[WEB_URI] = uri.format(CSV_NOM=CSV_NOM, CSV_PRENOM=CSV_PRENOM, WEB_NUMERO=WEB_NUMERO,
                                        nom=ligne[CSV_NOM], prenom=ligne[CSV_PRENOM], numero=dernier)

        logging.info("Resultat de la recherche: {}".format(kwargs[WEB_CONTENU]))

    kwargs.update(APP_PATHS)

    return render_template('{}.html'.format(APP_ACCUEIL), **kwargs)


@app.route(APP_PATHS[APP_CHANGELOG])
def retourner_changelog():
    """Affiche les derniers changement sur le logiciel."""
    logging.info("Page de {}".format(APP_CHANGELOG))
    with open(CHEMIN_CHANGELOG, mode="r") as changelog:
        html = markdown(changelog.read())

    kwargs = {WEB_CONTENU: html, WEB_ACTIVE: APP_CHANGELOG}
    kwargs.update(APP_PATHS)
    return render_template("{}.html".format(APP_CHANGELOG), **kwargs)


@app.route(APP_PATHS[APP_EVENEMENT], methods=[WEB_GET, WEB_POST])
def retourner_evenement():
    """Enregistre un événement."""
    logging.info("Page de {}".format(APP_EVENEMENT))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    kwargs = {WEB_ACTIVE: APP_EVENEMENT}
    if request.method == WEB_POST and CSV_PARTICIPANTS not in request.form.keys():
        print(request.form)
        flash("Événement enregistré! Merci d'animer le FABLAB!")
        ligneCsv = {}
        # TODO continue from here
        ligneCsv[CSV_EVENEMENT] = request.form[CSV_EVENEMENT]
        ligneCsv[CSV_NOM] = request.form[CSV_NOM]
        ligneCsv[CSV_PRENOM] = request.form[CSV_PRENOM]
        ligneCsv[CSV_PRENOM] = request.form[CSV_PRENOM]
        ligneCsv[CSV_HEURE] = request.form[CSV_HEURE]
        ajouter_evenement(ligneCsv)
    if request.method == WEB_POST and CSV_PARTICIPANTS in request.form.keys():
        editer_evenement(request.form[CSV_EVENEMENT], request.form[CSV_DATE], int(request.form[CSV_PARTICIPANTS]))

    contenu = obtenir_derniers_evenements(10)
    print(contenu)
    kwargs[WEB_CONTENU] = contenu
    kwargs.update(APP_PATHS)
    return render_template("{}.html".format(APP_EVENEMENT), **kwargs)


# TODO add the new adherent signup page
@app.route(APP_PATHS[APP_ADHESION])
def retourner_adhesion():
    logging.info("Page de {}".format(APP_ADHESION))
    # /adhesions/adhesions.php
    return render_template("501.html", active=APP_ADHESION, **APP_PATHS)


@app.route(APP_PATHS[APP_BUG], methods=[WEB_GET, WEB_POST])
def retourner_bug():
    """Telegram a bug."""
    logging.info("Page de {}".format(APP_BUG))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    if request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_ENVOYER:
        ligneCsv = {CSV_NOM: request.form[CSV_NOM], CSV_PRENOM: request.form[CSV_PRENOM],
                    CSV_DESCRIPTION: request.form[WEB_TEXTE]}
        ajouter_bug(ligneCsv)
        message = "Bug rapporté par {} {}\n{}".format(ligneCsv[CSV_PRENOM], ligneCsv[CSV_NOM],
                                                      ligneCsv[CSV_DESCRIPTION])
        TELEGRAM_API_MESSAGE_PAYLOAD["text"] = message
        r = get_url(TELEGRAM_API_URL, params=TELEGRAM_API_MESSAGE_PAYLOAD)
        if r.status_code == 200:
            flash("Telegram envoyé avec succès!")
        else:
            flash("Telegram non envoyé!")
        return redirect(url_for("retourner_accueil"))

    return render_template("{}.html".format(APP_BUG), active=APP_BUG, **APP_PATHS)


@app.route(APP_PATHS[APP_BUGS])
@login_required
def retourner_bugs():
    logging.info("Page de {}".format(APP_BUGS))

    kwargs = {WEB_ACTIVE: APP_BUGS, WEB_CONTENU: obtenir_bugs()}
    kwargs.update(APP_PATHS)
    return render_template("{}.html".format(APP_BUGS), **kwargs)


@app.route(APP_PATHS[APP_HISTORIQUE], methods=[WEB_GET, WEB_POST])
def retourner_historique():
    logging.info("Page de {}".format(APP_HISTORIQUE))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    kwargs = {}
    if request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_RECHERCHER:
        jour = request.form[WEB_JOUR]
        mois = request.form[WEB_MOIS]
        annee = request.form[WEB_ANNEE]
        kwargs[CSV_DATE] = "{}-{}-{}".format(annee, mois, jour)
    elif request.method == WEB_GET and request.args:
        date = request.args[CSV_DATE]
        dateTemporaire = datetime.strptime(date, '%Y-%m-%d').date()
        jourActuel = timedelta(days=int(request.args["delta"]))
        kwargs[CSV_DATE] = str(dateTemporaire + jourActuel)
    else:
        kwargs[CSV_DATE] = str(datetime.today().date())

    kwargs[WEB_CONTENU] = rechercher_entrees(jour=kwargs[CSV_DATE])

    kwargs["ceJour"] = str(datetime.now().date())
    kwargs["ceJour"] = "/historique?date={}&delta=0".format(kwargs["ceJour"])
    kwargs["suivant"] = "/{}?{}={}&delta=1".format(APP_HISTORIQUE, CSV_DATE, kwargs[CSV_DATE])
    kwargs["precedent"] = "/{}?{}={}&delta=-1".format(APP_HISTORIQUE, CSV_DATE, kwargs[CSV_DATE])
    kwargs[WEB_ACTIVE] = APP_HISTORIQUE
    kwargs.update(APP_PATHS)
    return render_template("{}.html".format(APP_HISTORIQUE), **kwargs)


def mise_a_jour_adherents(fichier):
    logging.info("Mise à jour adhérent")
    if fichier and allowed_file(fichier.filename):
        nomDuFichier = secure_filename(fichier.filename)
        cheminFichier = path.join(app.config["UPLOAD_FOLDER"], nomDuFichier)
        fichier.save(cheminFichier)
        test = test_fichier_csv(cheminFichier)
        if test is True:
            reecrire_registre_des_entrees(cheminFichier)
            flash("Fichier: {} téléversé!".format(nomDuFichier))
        else:
            flash("Erreur, fichier non compatible...")
            for text in test.split("\n"):
                flash(text)


@app.route(APP_PATHS[APP_ADMIN], methods=[WEB_POST])
@login_required
def retourner_admin():
    logging.info("Page de {}".format(APP_ADMIN))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    texte = "Espace Admin"
    dernier = lire_dernier()
    kwargs = {WEB_ACTIVE: APP_ADMIN, WEB_DERNIER: dernier}
    newKwargs = {}
    if request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_SUPPRIMER:
        numero = request.form[WEB_NUMERO]
        texte = supprimer_rfid_adherent(numero)
        flash(texte)
    elif request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_RECHERCHER:
        nom = request.form[CSV_NOM]
        # FIXME ajouter for associer? what to do with associer endpoint
        uri = "/{WEB_AJOUTER}?{CSV_NOM}={nom}&{CSV_PRENOM}={prenom}&{WEB_NUMERO}={numero}"
        texte, lignes = rechercher_adherent(nom, uri)
        for ligne in lignes:
            ligne[WEB_URI] = uri.format(ligne[CSV_NOM], ligne[CSV_PRENOM], dernier)
        newKwargs = {WEB_TEXTE: texte, CSV_NOM: nom, WEB_CONTENU: lignes}
    elif request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_ENTREE:
        nom = request.form[CSV_NOM]
        prenom = request.form[CSV_PRENOM]
        texte, lignes = rechercher_entrees(nom, prenom)
        newKwargs = {WEB_TEXTE: texte, CSV_NOM: nom, WEB_CONTENU: lignes}
    elif request.method == WEB_POST and request.form[WEB_BOUTON] == WEB_TELEVERSER:
        if "file" not in request.files:  # check if the post request has the file part
            flash("Pas de fichier...")
            return redirect(request.url)
        fichier = request.files["file"]
        if fichier.filename == "":  # if user does not select file, browser also submit an empty part without filename
            flash("Aucun fichier séléctionné")
            return redirect(request.url)

        mise_a_jour_adherents(fichier)

    kwargs.update(newKwargs)
    kwargs.update(APP_PATHS)
    return render_template("{}.html".format(APP_ADMIN), **kwargs)


@app.route("/{}".format(WEB_AJOUTER), methods=[WEB_GET, WEB_POST])
@login_required
def ajouter():
    """Associer un numero de badge RFID a un adherent"""
    logging.info("Page de {}".format(WEB_AJOUTER))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    kwargs = {WEB_ACTIVE: APP_ACCUEIL}

    if request.method == WEB_GET:
        kwargs[CSV_PRENOM] = request.args.get(CSV_PRENOM)
        kwargs[CSV_NOM] = request.args.get(CSV_NOM)
        kwargs[WEB_NUMERO] = request.args.get(WEB_NUMERO)
        kwargs[WEB_RECHERCHER] = "{} {}".format(kwargs[CSV_PRENOM], kwargs[CSV_NOM])

        if WEB_ACTION in request.args.keys() and request.args[WEB_ACTION] == WEB_ENTREE:
            kwargs[WEB_CONTENU] = rechercher_entrees(nom=kwargs[CSV_NOM], prenom=kwargs[CSV_PRENOM])
            kwargs.update(APP_PATHS)

            return render_template("{}.html".format(APP_ACCUEIL), **kwargs)
        else:
            ajouter_rfid_adherent(kwargs[CSV_NOM], kwargs[CSV_PRENOM], kwargs[WEB_NUMERO])
            flash("Association entre rfid '{}' et adhérent '{} {}' réussie.".format(
                kwargs[WEB_NUMERO], kwargs[CSV_PRENOM], kwargs[CSV_NOM]))

            return redirect(url_for("retourner_admin"))


@app.route("/{}".format(WEB_SIMULER), methods=[WEB_GET, WEB_POST])
def simuler():
    logging.info("Page de {}".format(WEB_SIMULER))
    if request.method:
        logging.info("Requête reçue:\nForm: {}\nArgs: {}".format(str(request.form), str(request.args)))

    kwargs = {WEB_ACTIVE: APP_ACCUEIL}
    if request.method == WEB_GET and request.args[CSV_NOM] and request.args[CSV_PRENOM] and request.args[WEB_NUMERO]:
        kwargs[CSV_PRENOM] = request.args.get(CSV_PRENOM)
        kwargs[CSV_NOM] = request.args.get(CSV_NOM)
        kwargs[WEB_RECHERCHER] = "{} {}".format(kwargs[CSV_PRENOM], kwargs[CSV_NOM])
        if not detecter_deja_scanne(kwargs[CSV_NOM], kwargs[CSV_PRENOM]):
            dateAdhesion = rechercher_date_adhesion(kwargs[CSV_NOM], kwargs[CSV_PRENOM])
            ajouter_entree(kwargs[CSV_NOM], kwargs[CSV_PRENOM], dateAdhesion)
            flash("Bonjour, {}! Bons projets!".format(kwargs[CSV_PRENOM]))
        else:
            flash("Bien tenté {} mais tu t'es déjà inscrit!".format(kwargs[CSV_PRENOM]))

        # kwargs.update(APP_PATHS)
        # kwargs[WEB_CONTENU] = rechercher_entrees(nom=kwargs[CSV_NOM], prenom=kwargs[CSV_PRENOM])
        logging.info("Redirection vers laccueil")
        return redirect(url_for("retourner_accueil"))


def allowed_file(filename):
    logging.info("Fichiers authorisés")
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=1)

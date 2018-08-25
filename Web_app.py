#!/usr/bin/env python3
# -*- coding: utf_8 -*-
from datetime import date, datetime, timedelta
from os import path
from re import compile as re_compile

from requests import get as get_url

from flask import (Flask, Response, flash, redirect, render_template, request,
                   url_for)
from flask_bootstrap import Bootstrap
from flask_security import (RoleMixin, Security, SQLAlchemyUserDatastore,
                            UserMixin, login_required)
from flask_sqlalchemy import SQLAlchemy
from modules.app_secrets import (SECRET_KEY, SECURITY_PASSWORD_SALT,
                                 TELEGRAM_API_CHAT_ID, TELEGRAM_API_TOKEN)
from modules.entree_sortie import (FICHIER_DES_ENTREES_CHEMIN, ajouter_email,
                                   ajouter_entree, ajouter_rfid_adherent,
                                   lire_dernier, rechercher_adherent,
                                   rechercher_date_adhesion,
                                   rechercher_entrees,
                                   reecrire_registre_des_entrees,
                                   supprimer_rfid_adherent, test_fichier_csv)
from redis import StrictRedis
from werkzeug.utils import secure_filename

# TODO turn entree sortie into a class


APP_ACCUEIL = "accueil"
APP_HISTORIQUE = "historique"
APP_ADMIN = "admin"
APP_LOGIN = "login"
APP_LOGOUT = "logout"
APP_VISITEUR = "visiteur"
APP_BUG = "bug"
APP_NEWS = "newsletter"
APP_ADHESION = "adhesion"
APP_EMAIL = "etienne.pouget@outlook.com"

APP_PATHS = {
    APP_ACCUEIL: "/" + APP_ACCUEIL,
    APP_HISTORIQUE: "/" + APP_HISTORIQUE,
    APP_ADMIN: "/" + APP_ADMIN,
    APP_LOGIN: "/" + APP_LOGIN,
    APP_LOGOUT: "/" + APP_LOGOUT,
    APP_VISITEUR: "/" + APP_VISITEUR,
    APP_BUG: "/" + APP_BUG,
    APP_NEWS: "/" + APP_NEWS,
    APP_ADHESION: "/" + APP_ADHESION
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
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['csv', 'txt'])


# Ne pas ajouter d'extensions au dessus
app = Flask(__name__)
# Extensions:
Bootstrap(app)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECURITY_PASSWORD_SALT'] = SECURITY_PASSWORD_SALT
app.config['SECURITY_POST_LOGIN_VIEW'] = APP_ADMIN
app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'login_user.html'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


redis = StrictRedis(host='localhost', port=6379, db=0)


def event_stream():
    pubsub = redis.pubsub()
    pubsub.subscribe("stream")
    # TODO: handle client disconnection.
    for message in pubsub.listen():
        print("Nouvelle entrée: {}".format(message))
        jsMessage = message["data"]
        if isinstance(jsMessage, int):
            continue
        message = message["data"].decode()
        match = STREAM_TYPE.match(message)
        type = match.group(1)
        jsMessage = match.group(2)
        if "non repertorié" in jsMessage:
            jsMessage += BOUTON_AJOUT_BADGE.format(APP_PATHS[APP_ADMIN])
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
def redirgiger_accueil():
    return redirect(url_for("retourner_accueil"))


@app.route('/stream')
def stream():
    return Response(event_stream(), mimetype="text/event-stream")


@app.route('/accueil')
def retourner_accueil():
    """Affiche les entrées du jour sur la page d'accueil."""
    jour = str(date.today())

    entreesDuJour = rechercher_entrees(jour=jour)

    return render_template('accueil.html',
                           contenu=entreesDuJour,
                           cherche=jour,
                           active="accueil",
                           **APP_PATHS)


# TODO add the new adherent signup page
@app.route("/adhesion")
def retourner_adhesion():
    return render_template("501.html",
                           active="adhesion",
                           **APP_PATHS)


# TODO add a page to submit a bug report or a feature request
@app.route("/bug", methods=['GET', 'POST'])
def retourner_bug():
    """Telegram a bug."""
    if request.method == 'POST' and request.form['bouton'] == "envoyer":
        message = request.form['text']
        TELEGRAM_API_MESSAGE_PAYLOAD["text"] = message
        r = get_url(TELEGRAM_API_URL, params=TELEGRAM_API_MESSAGE_PAYLOAD)
        if r.status_code == 200:
            flash("Telegram envoyé avec succès!")
        else:
            flash("Telegram non envoyé!")
        return redirect(url_for("retourner_accueil"))

    return render_template("bug.html",
                           active="bug",
                           **APP_PATHS)


@app.route('/historique', methods=['GET', 'POST'])
def retourner_historique():
    ceJour = str(datetime.now().date())
    ceJour = '/changer?date={}&delta=0'.format(ceJour)
    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        print("histoire")
        jour = request.form['jour']
        mois = request.form['mois']
        annee = request.form['annee']
        date = "{}-{}-{}".format(annee, mois, jour)
        suivant = '/changer?date={}&delta=1'.format(date)
        precedent = '/changer?date={}&delta=-1'.format(date)
        entreesDuJour = rechercher_entrees(jour=date)
    else:
        precedent = suivant = entreesDuJour = None
        date = str(datetime.today().date())

    suivant = '/changer?date={}&delta=1'.format(date)
    precedent = '/changer?date={}&delta=-1'.format(date)

    return render_template('historique.html',
                           active="historique",
                           precedent=precedent,
                           suivant=suivant,
                           ceJour=ceJour,
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

    entreesDuJour = rechercher_entrees(jour=date)

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
                               dernier=dernier,
                               **APP_PATHS)

    elif request.method == 'POST' and request.form['bouton'] == "rechercher":
        nom = request.form['nom']
        # FIXME ajouter for associer? what to do with associer endpoint
        uri = "/ajouter?nom={}&prenom={}"
        texte, lignes = rechercher_adherent(nom, uri)
        for ligne in lignes:
            ligne.insert(-1, dernier)
            ligne[-1] += "&numero={}".format(dernier)
            print(ligne)

        return render_template('admin.html',
                               dernier=dernier,
                               texte=texte,
                               nom=nom,
                               active="admin",
                               contenu=lignes,
                               **APP_PATHS)
    elif request.method == 'POST' and request.form['bouton'] == "televerser":
        print(request.files, request.form)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('Pas de fichier...')
            return redirect(request.url)
        fichier = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if fichier.filename == '':
            flash('Aucun fichier séléctionné')
            return redirect(request.url)

        if fichier and allowed_file(fichier.filename):
            nomDuFichier = secure_filename(fichier.filename)
            cheminFichier = path.join(app.config['UPLOAD_FOLDER'], nomDuFichier)
            fichier.save(cheminFichier)
            test = test_fichier_csv(cheminFichier)
            if test is True:
                reecrire_registre_des_entrees(cheminFichier)
                flash("Fichier: {} téléversé!".format(nomDuFichier))
            else:
                flash("Erreur, fichier non compatible...")
                for text in test.split("\n"):
                    flash(text)

        return render_template("admin.html",
                               active="admin",
                               dernier=dernier,
                               **APP_PATHS)
    else:
        return render_template('admin.html',
                               active="admin",
                               dernier=dernier,
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
            lignes = rechercher_entrees(nom=nom, prenom=prenom)

            return render_template('accueil.html',
                                   contenu=lignes,
                                   cherche=cherche,
                                   active="accueil",
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
        entrees = rechercher_entrees(nom=nom, prenom=prenom)

        return render_template('accueil.html',
                               contenu=entrees,
                               cherche=cherche,
                               active="accueil",
                               **APP_PATHS)

    return redirect(url_for('retourner_admin'))


@app.route('/sans_badge', methods=['GET', 'POST'])
def sans_badge():
    if request.method == "POST":
        prenom = request.args.get('prenom')
        nom = request.args.get('nom')
        ajouter_entree(nom, prenom)

    return redirect(url_for("retourner_accueil"))


@app.route("/visiteur", methods=["GET", "POST"])
def pagevisiteur():
    dernier = lire_dernier()
    if request.method == "POST" and request.form["bouton"] == "visiteur":
        prenom = request.form["prenom"]
        nom = request.form["nom"]
        email = request.form["email"]
        if email:
            ajouter_email(nom, prenom, email)
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

        return render_template('visiteur.html',
                               dernier=dernier,
                               texte=texte,
                               active="visiteur",
                               contenu=lignes,
                               **APP_PATHS)

    else:
        return render_template('visiteur.html',
                               active="visiteur",
                               **APP_PATHS)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(host="0.0.0.0")

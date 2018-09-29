#!/usr/bin/env python3
# -*- coding: utf_8 -*-
from datetime import date, datetime, timedelta
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
from modules.entree_sortie import (ajouter_bug, ajouter_email, ajouter_entree,
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
from werkzeug.utils import secure_filename

# TODO turn entree sortie into a class


NOM = "NOM"
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
    APP_BUGS: "/" + APP_BUGS
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


# Setup stats
def flask_update_stats():
    g.visiteurCeJour, g.visiteurCetteSemaine, g.visiteurCeMois = update_stats()


app.before_request(flask_update_stats)


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

    return render_template('accueil.html', contenu=entreesDuJour, cherche=jour, active="accueil", **APP_PATHS)


@app.route("/changelog")
def retourner_changelog():
    """Affiche les derniers changement sur le logiciel."""
    with open("CHANGELOG.md", mode='r') as changelog:
        html = markdown(changelog.read())

    kwargs = {"content": html, "active": "changelog"}
    kwargs.update(APP_PATHS)
    return render_template("changelog.html", **kwargs)


@app.route("/evenement", methods=["GET", "POST"])
def retourner_evenement():
    """Enregistre un événement."""
    kwargs = {"active": "evenement"}
    if request.method == "POST" and "participants" not in request.form.keys():
        print(request.form)
        flash("Événement enregistré! Merci d'animer le FABLAB!")
        ligneCsv = {}
        ligneCsv["Evenement"] = request.form["evenement"]
        ligneCsv[NOM] = request.form[NOM]
        ligneCsv["Prenom"] = request.form["prenom"]
        ligneCsv["Date"] = request.form["date"]
        ligneCsv["Heure"] = request.form["heure"]
        ajouter_evenement(ligneCsv)
    if request.method == "POST" and "participants" in request.form.keys():
        editer_evenement(request.form["evenement"], request.form["date"], int(request.form["participants"]))

    contenu = obtenir_derniers_evenements(10)
    print(contenu)
    kwargs["contenu"] = contenu
    kwargs.update(APP_PATHS)
    return render_template("evenement.html", **kwargs)


# TODO add the new adherent signup page
@app.route("/adhesion")
def retourner_adhesion():
    return render_template("501.html", active="adhesion", **APP_PATHS)


@app.route("/bug", methods=['GET', 'POST'])
def retourner_bug():
    """Telegram a bug."""
    if request.method == 'POST' and request.form['bouton'] == "envoyer":
        ligneCsv = {NOM: request.form[NOM], "Prenom": request.form["prenom"],
                    "Description": request.form["text"]}
        ajouter_bug(ligneCsv)
        message = "Bug rapporté par {} {}\n{}".format(ligneCsv["Prenom"], ligneCsv[NOM], ligneCsv["Description"])
        TELEGRAM_API_MESSAGE_PAYLOAD["text"] = message
        r = get_url(TELEGRAM_API_URL, params=TELEGRAM_API_MESSAGE_PAYLOAD)
        if r.status_code == 200:
            flash("Telegram envoyé avec succès!")
        else:
            flash("Telegram non envoyé!")
        return redirect(url_for("retourner_accueil"))

    return render_template("bug.html", active="bug", **APP_PATHS)


@app.route('/bugs')
@login_required
def retourner_bugs():
    kwargs = {"active": "bugs", "contenu": obtenir_bugs()}
    kwargs.update(APP_PATHS)
    return render_template("bugs.html", **kwargs)


@app.route('/historique', methods=['GET', 'POST'])
def retourner_historique():
    kwargs = {}
    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        jour = request.form['jour']
        mois = request.form['mois']
        annee = request.form['annee']
        kwargs["date"] = "{}-{}-{}".format(annee, mois, jour)
    elif request.method == "GET" and request.args:
        date = request.args.get('date')
        dateTemporaire = datetime.strptime(date, '%Y-%m-%d').date()
        jourActuel = timedelta(days=int(request.args["delta"]))
        kwargs["date"] = str(dateTemporaire + jourActuel)
    else:
        kwargs["date"] = str(datetime.today().date())
        print("HELLO")

    kwargs["contenu"] = rechercher_entrees(jour=kwargs["date"])

    kwargs["ceJour"] = str(datetime.now().date())
    kwargs["ceJour"] = '/historique?date={}&delta=0'.format(kwargs["ceJour"])
    kwargs["suivant"] = '/historique?date={}&delta=1'.format(kwargs["date"])
    kwargs["precedent"] = '/historique?date={}&delta=-1'.format(kwargs["date"])
    kwargs["active"] = "historique"
    kwargs.update(APP_PATHS)
    return render_template('historique.html', **kwargs)


def mise_a_jour_adherents(fichier):
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


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def retourner_admin():
    texte = 'Espace Admin'
    dernier = lire_dernier()
    kwargs = {"active": "admin", "dernier": dernier}
    newKwargs = {}
    if request.method == 'POST' and request.form['bouton'] == "supprimer":
        numero = request.form['numero']
        texte = supprimer_rfid_adherent(numero)
        flash(texte)
    elif request.method == 'POST' and request.form['bouton'] == "rechercher":
        nom = request.form[NOM]
        # FIXME ajouter for associer? what to do with associer endpoint
        uri = "/ajouter?NOM={}&prenom={}&numero={}"
        texte, lignes = rechercher_adherent(nom, uri)
        for ligne in lignes:
            ligne["uri"] = uri.format(ligne[NOM], ligne["Prenom"], dernier)
        newKwargs = {"texte": texte, NOM: nom, "contenu": lignes}
    elif request.method == 'POST' and request.form['bouton'] == "entree":
        nom = request.form[NOM]
        prenom = request.form["prenom"]
        texte, lignes = rechercher_entrees(nom, prenom)
        newKwargs = {"texte": texte, NOM: nom, "contenu": lignes}
    elif request.method == 'POST' and request.form['bouton'] == "televerser":
        if 'file' not in request.files:  # check if the post request has the file part
            flash('Pas de fichier...')
            return redirect(request.url)
        fichier = request.files['file']
        if fichier.filename == '':  # if user does not select file, browser also submit an empty part without filename
            flash('Aucun fichier séléctionné')
            return redirect(request.url)

        mise_a_jour_adherents(fichier)

    kwargs.update(newKwargs)
    kwargs.update(APP_PATHS)
    return render_template('admin.html', **kwargs)


@app.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter():
    kwargs = {"active": "accueil"}

    if request.method == "GET":
        kwargs["prenom"] = request.args.get('prenom')
        kwargs[NOM] = request.args.get(NOM)
        kwargs["numero"] = request.args.get('numero')
        kwargs["cherche"] = "{} {}".format(kwargs["prenom"], kwargs[NOM])

        if "action" in request.args.keys() and request.args['action'] == "entree":
            kwargs["contenu"] = rechercher_entrees(nom=kwargs[NOM], prenom=kwargs["prenom"])
            kwargs.update(APP_PATHS)

            return render_template('accueil.html', **kwargs)
        else:
            ajouter_rfid_adherent(kwargs[NOM], kwargs["prenom"], kwargs["numero"])
            flash("Association entre rfid '{}' et adhérent '{} {}' réussie.".format(
                kwargs["numero"], kwargs["prenom"], kwargs[NOM]))

            return redirect(url_for('retourner_admin'))


@app.route('/simuler', methods=['GET', 'POST'])
def simuler():
    kwargs = {"active": "accukwargseil"}
    if request.method == "GET" and request.args[NOM] and request.args["prenom"] and request.args["numero"]:
        kwargs["prenom"] = request.args.get('prenom')
        kwargs[NOM] = request.args.get(NOM)
        kwargs["cherche"] = "{} {}".format(kwargs["prenom"], kwargs[NOM])
        if not detecter_deja_scanne(kwargs[NOM], kwargs["prenom"]):
            dateAdhesion = rechercher_date_adhesion(kwargs[NOM], kwargs["prenom"])
            ajouter_entree(kwargs[NOM], kwargs["prenom"], dateAdhesion)
            flash("Bonjour, {}! Bons projets!".format(kwargs["prenom"]))
        else:
            flash("Bien tenté {} mais tu t'es déjà inscrit!".format(kwargs["prenom"]))

        kwargs.update(APP_PATHS)
        kwargs["contenu"] = rechercher_entrees(nom=kwargs[NOM], prenom=kwargs["prenom"])
        return render_template('accueil.html', **kwargs)


@app.route("/visiteur", methods=["GET", "POST"])
def pagevisiteur():
    dernier = lire_dernier()
    kwargs = {"active": "visiteur", "dernier": dernier}
    if request.method == "POST" and request.form["bouton"] == "visiteur":
        ligneCsv = {"Prenom": request.form["prenom"], NOM: request.form[NOM],
                    "Email": request.form["email"], "Organisme": request.form["organisme"]}
        if ligneCsv["Email"]:
            ajouter_email(ligneCsv[NOM], ligneCsv["Prenom"], ligneCsv["Email"])

        if not detecter_deja_scanne(ligneCsv[NOM], ligneCsv["Prenom"]):
            ajouter_entree(ligneCsv[NOM], ligneCsv["Prenom"], "visiteur")
            flash("Bonjour, {}! Bons projets!".format(ligneCsv["Prenom"]))
        else:
            flash("Bien tenté {} mais tu t'es déjà inscrit!".format(ligneCsv["Prenom"]))

        return redirect(url_for('retourner_accueil'))

    if request.method == 'POST' and request.form['bouton'] == "rechercher":
        kwargs[NOM] = request.form[NOM]
        uri = "/simuler?NOM={}&prenom={}&numero={}"
        kwargs["texte"], kwargs["contenu"] = rechercher_adherent(kwargs[NOM], uri)
        for ligne in kwargs["contenu"]:
            ligne["uri"] = uri.format(ligne[NOM], ligne["Prenom"], dernier)

    kwargs.update(APP_PATHS)

    return render_template('visiteur.html', **kwargs)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=0)

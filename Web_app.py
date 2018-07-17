from flask import Flask,render_template,request,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, utils
from flask_bootstrap import Bootstrap
from os import getcwd
import time
import csv

fichier_adherent = '/home/pi/Documents/test.csv'
sortie = '/home/pi/Documents/sortie.txt'
accueil = "/"
historique = "/historique"
admin = "/admin"
login = '/login'
logout = '/logout'

#En paramètre, mettre sous ce format : chaine = ["prenom","nom',"numero"]
def ecriture(chaine):
	fichier = open(fichier_adherent, "a")
	ecriture = csv.writer(fichier)
	ecriture.writerow(chaine)
	fichier.close()


def supprimer_ligne(chaine):
	contenu = ""

	fichier_supprimer = open(fichier_adherent,"r")
	for ligne in fichier_supprimer:
		if not(chaine in ligne):
			contenu += ligne
	fichier_supprimer.close()
 
	fichier_ecrire = open(fichier_adherent, 'w')
	fichier_ecrire.write(contenu)
	fichier_ecrire.close()

#Ne pas ajouter d'extensions au dessus
app = Flask(__name__)
#Extensions: 
Bootstrap(app)
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SECURITY_PASSWORD_SALT'] = 'zedzoedajdpaok'
app.config['SECURITY_POST_LOGIN_VIEW']= admin
app.config['SECURITY_LOGIN_USER_TEMPLATE']= 'login_user.html'


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
# Create a user to test with
@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(email='hatlab', password='hatlab')
    db.session.commit()


@app.route('/')
def retourner_accueil():
    contenu =[]
    jour = time.strftime("%d %B %Y")
    for line in open (sortie):
        if jour in line:
            ligne = line.split(' ')
            contenu.append(ligne[4])
            contenu.append(ligne[5])
            contenu.append(ligne[6])
            

    return render_template('accueil.html',accueil=accueil,historique=historique,contenu=contenu,jour=jour,admin=admin,logout = logout)
    
@app.route('/historique')    
def retourner_historique():
    return render_template('historique.html',accueil=accueil,historique=historique,admin=admin,logout = logout)

@app.route('/ajouter', methods=['GET','POST'])
@login_required
def ajouter_adherent():
    if request.method =='POST':
        prenom=request.form['prenom']
        nom =request.form['nom']
        numero=request.form['numero']
        chaine_a_envoyer = [numero,prenom,nom]
        ecriture(chaine_a_envoyer)
        return render_template('confirmation.html',accueil=accueil,historique=historique,login=login,prenom=prenom,nom=nom,numero=numero,logout = logout)

    else: return render_template('ajouter.html',accueil=accueil,historique=historique,admin=admin,logout = logout)
 
 
@app.route('/supprimer', methods=['GET','POST'])
@login_required
def supprimer_adherent():
    compteur=0
    if request.method=='POST':
        
        numero = request.form['numero']
        for line in open (fichier_adherent):
            if numero in line:
                ligne= line.split(',')
                texte = "Vous avez supprimé l'adhérent "+ ligne[1]+ " "+ligne[2]+" au numéro " + ligne[0]
                compteur+=1
                
        if compteur==0:
            texte = "Pas d'adhérent associé à ce numéro"
        
        
        supprimer_ligne(numero)
        
        return render_template('confirmation2.html', accueil=accueil,historique=historique,admin=admin,texte=texte,logout = logout)
    
    else : return render_template('supprimer.html', accueil=accueil,historique=historique,admin=admin,logout = logout)



@app.route('/admin')
@login_required
def retourner_admin():      
    return  render_template('admin.html',accueil=accueil,historique=historique,admin=admin,logout = logout)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        print(request.form['msg'])
        return "Vous avez envoyé : {msg}".format(msg=request.form['msg'])
    
    return '<form action="" method="post"><input type="password" name="msg" /><input type="submit" value="Envoyer" /></form>'


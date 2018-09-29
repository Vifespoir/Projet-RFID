# Installation

## En cas de bugs

### L'application ne se lance pas

Redémarrer l'orangepi. Si ça ne marche toujours pas contacter le bureau.

### Le système est lancé mais Firefox est fermé ou l'onglet badgeuse est fermé

Redémarrer Firefox, le fermer et l'ouvrir.

### Il y a un bug dans l'application

Le rapporter sous le menu `bug`.

### La touche "@" ne marche pas

C'est un problème de keyboard layout. Ouvrir un terminal et y taper: `sudo dpkg-reconfigure keyboard-configuration`. Suivre les instructions. Choisir touche `alt-gr` = `alt droite`.

## Installation du programme badgeuse:
```
# installation des dépendances système
sudo aptitude install bcrypt python3 python3-pip python3-dev python3-bcrypt
# installation des dépendances python
sudo pip install setuptools
# copie du projet git
git clone https://github.com/Vifespoir/Projet-RFID
# installation des dépendances python3
sudo pip3 install -r requirements.txt
```

## Lancement du service au démarrage:

Ajout de Firefox au programme qui se lance au démarrage:

* Menu démarrer -> accessoire -> Trouver un programme -> taper `startup` dans la barre de recherche
* ajouter un programme -> nom: `Firefox` -> execute: `firefox`

Ajout d'un cron job pour lancer la badgeuse au démarrage:

```
sudo crontab -e
```

Ajouter les lignes suivante au fichier:

```
# Lancement de l'application badgeuse au démarrage de l'orangepi
@reboot /home/sqylab/Projet-RFID/start-jobs.sh
```
Attention si changement du nom d'utilisateur il faudra éditer le chemin.

## Paramétrage du port SPI

### CHANGELOG
<hr>

#### EN COURS DE RESOLUTION
<hr>

* Utiliser werkzeug pour augmenter la securité
* API
* Graphiques
* Convertir csv en base de donnée
* Heure de fermeture - bouton shutdown
* Adhérent en cours de traitement

#### IMPOSSIBLE A RESOUDRE
<hr>
Données manquante:

* Rajouter numero adherent dans le fichier historique
* Rajouter les logo HATLAB et SQYLAB

Non nécessaire:

* Rajouter "boite à idées" -- **Redondance possible avec "Bug/Suggestion"**
* Ajouter un cronjob pour se mettre à jour à distance

#### RESOLU
<hr>

Date 29 septembre 2018

* Ajouter un fichier README.md avec les instructions de debuggage et d'Installation
* Corriger le bug du @ (voir README.md)
* Changer

Date: 4 septembre 2018

* CORRIGER: L'heure d'entrée des visiteurs est toujours à 00h00
* CORRIGER: Numéro de badge peut etre associer deux fois...
* CORRIGER: Possibilité de simuler plusieurs fois de suite un badge, ajouter un timer
* AMELIORATION: Un badge ou un adhérent, ne peut scanner ou simuler un scan qu'une fois toutes les deux heures, même chose pour les visiteurs
* AMELIORATION: lecture csv en utilisant l'entête (première ligne du fichier)
* AMELIORATION: Le menu de navigation reste visible tout le temps + amélioration du css
* AMELIORATION: pour les visiteurs rajouter champ "organisme"
* AMELIORATION: compteur visiteur, ATTENTION compteur roulant et non de lundi à dimanche ou du premier au premier
* AMELIORATION: Ajout d'une page événement avec possibilité d'ajouter le nombre de participants
* AMELIORATION: Ajout d'un rapport de bug dans la partie administration
* AMELIORATION: Ajout d'un timeout pour desauthentifier l'admin

#### RESOLU - DEJA INCLU
<hr>

#### NON RESOLU - MANQUE DE DETAIL
<hr>

* Voici le message recu quand Brigitte LUYPAERT essaye de se connecter ! : Espace sans badge / visiteur ID du dernier badge : 192132106161

import csv
fichier = '/home/pi/Documents/test.csv'
nom = 'Michel'

def supprimer_ligne(chaine):
	contenu = ""

	fichier_supprimer = open(fichier,"r")
	for ligne in fichier_supprimer:
		if not(chaine in ligne):
			contenu += ligne
	fichier_supprimer.close()
 
	fichier_ecrire = open(fichier, 'w')
	fichier_ecrire.write(contenu)
	fichier_ecrire.close()


supprimer_ligne(nom)

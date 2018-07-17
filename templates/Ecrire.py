import csv
fichier = '/home/pi/Documents/test.csv'
prenom = 'clement'
nom = 'berle'
numero = 'oui'
chaaine = ["clement","berle","11151622"]

def ecriture(chaine):
	oui = open(fichier, "a")
	test = csv.writer(oui)
	test.writerow(chaine)
	oui.close()

ecriture(chaaine)

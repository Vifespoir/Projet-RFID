import csv
import os
fichier = '/home/pi/Documents/test.csv'

contenu =[]
with open(fichier,'rb') as fichier_read:
	reader = csv.reader(fichier_read)
	chaine = "Pas d'ahdérents à ce nom"
	for line in reader:
		if 'AMMAR' in line:
			contenu.append(ligne[2])
            contenu.append(ligne[1])
            contenu.append(ligne[5])

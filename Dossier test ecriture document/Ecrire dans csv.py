import csv
import os
fichier = '/home/pi/Documents/est.csv'
fichier_temp= '/home/pi/Documents/fichier_temporaire.csv'
toto =''
code = 123456789
def ecrire(chaine):
	with open(fichier_temp, 'a') as ecriture:
		test = csv.writer(ecriture)
		test.writerow(chaine)


with open(fichier,'rb') as fichier_read:
	reader = csv.reader(fichier_read)
	for line in reader:
		chaine = [line[0],line[1],line[2],line[3],line[4],line[5]]
		if line[1]=='AMMAR':
			if line[2]=='Ramzi':
				chaine = [line[0],line[1],line[2],line[3],line[4], code]
		ecrire(chaine)

#os.rename('/home/pi/Documents/fichier_temporaire.csv','/home/pi/Documents/test.csv')

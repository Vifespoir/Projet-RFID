import datetime
from datetime import date
from datetime import datetime
import time
fichier = '/home/pi/Documents/test.csv'
sortie = '/home/pi/Documents/sortie.txt'

            
def faire_string(ligne):
        ligne = line.split(',')
        date_cotisation = datetime.strptime(ligne[4],'%d/%m/%Y')
        date = date_cotisation.date()
        difference = date.today() - date
        print(difference.days)
        if difference.days >365:
            texte = ' Oui'
        else : texte = ' Date_de_cotisation_depassee'
        date = time.strftime("%A %d %B %Y %H:%M")
        return '\n' +  date +' '+ ligne[2] + ' ' + ligne[1] + texte

for line in open (fichier):
        if 'FAUVET' in line:
            test = open(sortie,'a')
            entree = faire_string(line)
            test.write(entree)
            test.close()
           


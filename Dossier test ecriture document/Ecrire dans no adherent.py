import datetime
import time
fichier = '/home/pi/Documents/test.csv'
sortie = '/home/pi/Documents/non_repertorie.txt'

code = '123456789'

date = time.strftime("%A %d %B %Y %H:%M")
test = open(sortie,'w')
entree = date + ' NoAdherent ' + code 
test.write(code)
test.close()

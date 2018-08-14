with open(vrai_fichier_adherent,'r') as fichier_read:
                reader = csv.reader(fichier_read)
                for line in reader:
                    if cherche in line:
                        compteur+=1
                        contenu.append(line[2])
                        contenu.append(line[1])
                        contenu.append(line[5])

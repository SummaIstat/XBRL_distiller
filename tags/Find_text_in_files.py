import os

def cerca_stringa(cartella, stringa):
    risultati = []

    # Scansione di tutti i file nella cartella
    for root, dirs, files in os.walk(cartella):
        for file in files:
            # Percorso completo del file
            percorso_file = os.path.join(root, file)

            # Apertura del file in modalità lettura
            with open(percorso_file, 'r') as f:
                # Lettura del contenuto del file
                contenuto = f.read()

                # Verifica della presenza della stringa nel contenuto
                if stringa in contenuto:
                    risultati.append(percorso_file)

    return risultati

# Esempio di utilizzo
#cartella_target = "C:/py/XBRL_distiller/tags/2018-11-04"
cartella_target = "C:/ISTAT/TF_xbrl/dati/p4_orig"
stringa_da_cercare = "contextRef"


risultati = cerca_stringa(cartella_target, stringa_da_cercare)
if len(risultati) > 0:
    print("Stringa trovata nei seguenti file:")
    for risultato in risultati:
        print(risultato)
else:
    print("La stringa non è stata trovata in nessun file.")
# Importăm bibliotecile necesare
import heapq  # Pentru a folosi heap-ul (coada de priorități) pentru calculul penalităților
import os  # Pentru a lucra cu fișiere și directoare
import numpy as np  # Pentru a folosi matricele și operațiile pe matrice din NumPy
import csv  # Pentru a lucra cu fișiere CSV
import re  # Pentru a folosi expresii regulate pentru a extrage numere din text

# Funcția citire va citi datele din fișierul dat și le va organiza într-un dicționar
def citire(cale_fisier):
    # Deschidem fișierul și citim toate liniile
    with open(cale_fisier, 'r') as fisier:
        linii = fisier.readlines()

    # Inițializăm listele pentru oferta, cerere și costuri
    oferta = []
    cerere = []
    costuri = []
    costuri_fixe = []
    costuri_fixe_magazine = []

    # Citim valorile pentru oferta și costuri fixe
    for linie in linii:
        linie = linie.strip()  # Eliminăm spațiile de la începutul și sfârșitul liniei
        # Dacă linia conține oferta, o adăugăm
        if linie.startswith('SCj'):
            oferta = list(map(int, re.findall(r'\d+', linie)))
        # Dacă linia conține costurile fixe pentru fiecare magazin, le adăugăm
        elif linie.startswith('Fj'):
            costuri_fixe = list(map(int, re.findall(r'\d+', linie)))
        # Dacă linia conține cererea, o adăugăm
        elif linie.startswith('Dk'):
            cerere = list(map(int, re.findall(r'\d+', linie)))

    # Citim costurile (Cjk), adică costurile de transport între fiecare magazin și client
    linii_cjk = []
    start_cjk = False
    for linie in linii:
        linie = linie.strip()
        # Dacă linia conține începutul secțiunii Cjk, o salvăm
        if linie.startswith('Cjk = [['):
            start_cjk = True
            linii_cjk.append(linie)
        elif start_cjk:
            # Continuăm să citim liniile până găsim sfârșitul secțiunii
            linii_cjk.append(linie)
            if linie.endswith(']];'):
                break

    rand_curent = []  # Vom adăuga valorile costurilor pentru fiecare magazin
    for linie in linii_cjk:
        # Extragem numerele din linie și le adăugăm în rand_curent
        numere = list(map(int, re.findall(r'\d+', linie)))
        rand_curent.extend(numere)
        # Când avem suficient de multe numere pentru un rând, le adăugăm la matricea de costuri
        while len(rand_curent) >= len(cerere):
            costuri.append(rand_curent[:len(cerere)])
            rand_curent = rand_curent[len(cerere):]

    # D și R sunt numărul de magazine și numărul de clienți
    d = len(oferta)
    r = len(cerere)

    # Citirea costurilor fixe pentru magazine (Fjk)
    linii_fjk = []
    start_fjk = False
    for linie in linii:
        linie = linie.strip()
        # Dacă linia conține începutul secțiunii Fjk, o salvăm
        if linie.startswith('Fjk = [['):
            start_fjk = True
            linii_fjk.append(linie)
        elif start_fjk:
            # Continuăm să citim liniile până găsim sfârșitul secțiunii
            linii_fjk.append(linie)
            if linie.endswith(']];'):
                break

    rand_curent = []
    for linie in linii_fjk:
        # Extragem numerele din linie și le adăugăm în rand_curent
        numere = list(map(int, re.findall(r'\d+', linie)))
        rand_curent.extend(numere)
        # Când avem suficient de multe numere pentru un rând, le adăugăm la costurile fixe ale magazinului
        while len(rand_curent) >= len(cerere):
            costuri_fixe_magazine.append(rand_curent[:len(cerere)])
            rand_curent = rand_curent[len(cerere):]

    # Returnăm toate datele sub forma unui dicționar
    return {
        "d": d,
        "r": r,
        "SCj": oferta,
        "Fj": costuri_fixe,
        "Dk": cerere,
        "Cjk": costuri,
        "Fjk": costuri_fixe_magazine
    }

# Funcția pentru a rezolva problema de transport folosind metoda penalităților
def prob_transport(d, r, SCj, Fj, Dk, Cjk, Fjk):
    copie_Cjk = [row[:] for row in Cjk]  # Facem o copie a matricei costurilor Cjk
    solutie_transport = np.zeros((d, r), dtype=int)  # Creăm o matrice pentru soluția de transport
    cost_total = 0  # Inițializăm costul total

    complet_rând = [False] * d  # Lista pentru a verifica dacă un magazin a fost completat
    complet_coloană = [False] * r  # Lista pentru a verifica dacă un client a fost completat

    penalități_rând = []  # Vom stoca penalitățile pentru rânduri (magazine)
    penalități_coloană = []  # Vom stoca penalitățile pentru coloane (clienți)

    # Funcție pentru a calcula penalitatea minimă pentru un rând sau o coloană
    def calc_penalitate_minim(costuri, complet):
        if complet:
            return 0
        valori = sorted([c for c in costuri if c != float('inf')])  # Sortăm costurile, ignorând infinitul
        if len(valori) >= 2:
            return valori[1] - valori[0]  # Diferența dintre cele două cele mai mici costuri
        elif len(valori) == 1:
            return valori[0]  # Dacă există doar un cost, îl returnăm direct
        return 0

    # Calculăm penalitățile pentru fiecare rând și coloană
    for i in range(d):
        if not complet_rând[i]:
            penalități_rând.append(
                (calc_penalitate_minim(Cjk[i], complet_rând[i]), i))
    for j in range(r):
        if not complet_coloană[j]:
            penalități_coloană.append((calc_penalitate_minim(
                [Cjk[i][j] for i in range(d)], complet_coloană[j]), j))

    # Creăm cozi de priorități pentru rânduri și coloane
    heapq.heapify(penalități_rând)
    heapq.heapify(penalități_coloană)

    # Algoritmul principal pentru rezolvarea problemei de transport
    while sum(SCj) > 0 and sum(Dk) > 0:
        if penalități_rând and (not penalități_coloană or penalități_rând[0][0] >= penalități_coloană[0][0]):
            # Alegem rândul cu penalitatea maximă
            penalitate_maximă, rând = heapq.heappop(penalități_rând)
            if SCj[rând] == 0:
                continue
            col = Cjk[rând].index(min(Cjk[rând]))  # Alegem coloana cu costul minim
        else:
            # Alegem coloana cu penalitatea maximă
            penalitate_maximă, col = heapq.heappop(penalități_coloană)
            if Dk[col] == 0:
                continue
            rând = min((Cjk[i][col], i)
                      for i in range(d) if not complet_rând[i])[1]  # Alegem rândul cu costul minim pentru coloana respectivă

        # Verificăm dacă există suficientă cerere și ofertă
        if SCj[rând] > 0 and Dk[col] > 0:
            cost = min(SCj[rând], Dk[col])  # Calculăm cât putem transporta
            solutie_transport[rând][col] = cost  # Stocăm soluția
            SCj[rând] -= cost  # Reducem oferta
            Dk[col] -= cost  # Reducem cererea

            if SCj[rând] == 0:
                complet_rând[rând] = True  # Marcam magazinul ca fiind completat
            if Dk[col] == 0:
                complet_coloană[col] = True  # Marcam clientul ca fiind completat

            # Calculăm costul total, inclusiv costurile fixe
            cost_total += cost * copie_Cjk[rând][col] + Fjk[rând][col]

            # Actualizăm penalitățile
            if not complet_rând[rând]:
                penalități_rând.append(
                    (calc_penalitate_minim(Cjk[rând], complet_rând[rând]), rând))
                heapq.heapify(penalități_rând)
            if not complet_coloană[col]:
                penalități_coloană.append((calc_penalitate_minim(
                    [Cjk[i][col] for i in range(d)], complet_coloană[col]), col))
                heapq.heapify(penalități_coloană)

    # Adăugăm costurile fixe pentru fiecare magazin la costul total
    cost_total += sum(Fj[j] for j in range(d) if any(solutie_transport[j]))

    return cost_total, solutie_transport.astype(int).tolist(), SCj, Dk

# Funcția pentru procesarea datelor din fișierele de intrare și salvarea rezultatelor într-un fișier CSV
def procesare_date(folder_input, fisier_csv):
    rezultate_csv = []

    # Verificăm dacă folderul de intrare există
    if not os.path.exists(folder_input):
        print(f"Eroare: Folderul de intrare '{folder_input}' nu exista.")
        return

    # Iterăm prin diferitele tipuri de instanțe și le procesăm
    for tip in ["small", "medium", "large"]:
        for num in range(1, 26):
            nume_fisier = f"Lab01_FCD_FCR_{tip}_{num:02d}.dat"  # Numele fișierului pentru fiecare instanță
            cale_fisier = os.path.join(folder_input, nume_fisier)  # Calea completă a fișierului
            if os.path.exists(cale_fisier):  # Dacă fișierul există
                print(f"Procesăm fișierul: {cale_fisier}")
                # Citim datele din fișier
                date = citire(cale_fisier)
                d, r = date["d"], date["r"]
                SCj, Fj, Dk = date["SCj"], date["Fj"], date["Dk"]
                Cjk, Fjk = date["Cjk"], date["Fjk"]

                # Apelăm funcția de rezolvare a problemei de transport
                cost_transport, solutie_transport, SCj_ramas, Dk_ramas = prob_transport(d, r, SCj, Fj, Dk, Cjk, Fjk)
                # Calculăm costul total, adăugând costurile fixe pentru fiecare magazin
                cost_total = cost_transport + sum(Fj)

                # Adăugăm rezultatul în lista de rezultate
                instance_nume = f"{tip}_instance_{num:02d}"
                rezultate_csv.append([instance_nume, cost_total])

    # Scriem rezultatele într-un fișier CSV
    header = ['Instanță', 'Cost Total']
    with open(fisier_csv, 'w', newline='', encoding='utf-8') as fisier:
        writer = csv.writer(fisier)
        writer.writerow(header)
        writer.writerows(rezultate_csv)
    print(f"Fișierul CSV a fost salvat cu succes: {fisier_csv}")

# Punctul de intrare al programului
if __name__ == "__main__":
    folder_input = "Lab_FCD_FCR_instances"  # Folderul care conține fișierele de intrare
    fisier_csv = "rezultate_cost_fix_both.csv"  # Numele fișierului CSV de ieșire
    procesare_date(folder_input, fisier_csv)  # Apelăm funcția pentru procesare
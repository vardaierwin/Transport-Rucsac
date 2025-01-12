import os
import re
import numpy as np
import csv

def citire(cale_fisier): # Citește un fișier .dat și returnează datele într-un format ușor de utilizat.
    # cale_fisier: Calea către fișierul .dat ce conține datele problemei.
    # return: Numărul de depozite, numărul de magazine, capacitățile depozitelor, cererea magazinelor, 
    # costurile de livrare și costurile fixe pentru magazine.

    # Citire fișier și extragerea liniilor text
    with open(cale_fisier, 'r') as fisier:
        linii = fisier.readlines()

    # Inițializare liste pentru datele problemei
    capacitate_depozite = []  # Capacitățile depozitelor (SCj)
    cerere_magazine = []      # Cererea magazinelor (Dk)
    costuri_livrare = []      # Costurile de livrare între depozite și magazine (Cjk)
    costuri_fixe_magazine = []  # Costurile fixe pentru magazine (Fjk)

    # Parcurgere linii pentru citirea capacităților și cererii
    for linie in linii:
        linie = linie.strip()  # Eliminare spații inutile
        if linie.startswith('SCj'):
            capacitate_depozite = list(map(int, re.findall(r'\d+', linie)))
        elif linie.startswith('Dk'):
            cerere_magazine = list(map(int, re.findall(r'\d+', linie)))

    # Citirea costurilor variabile de livrare (Cjk)
    linii_costuri = []
    start_costuri = False
    for linie in linii:
        linie = linie.strip()
        if linie.startswith('Cjk = [['):  # Începutul matricei Cjk
            start_costuri = True
            linii_costuri.append(linie)
        elif start_costuri:
            linii_costuri.append(linie)
            if linie.endswith(']];'):  # Sfârșitul matricei
                break

    # Procesare matrice Cjk
    rand_curent = []
    for linie in linii_costuri:
        valori = list(map(int, re.findall(r'\d+', linie)))  # Extragem valorile numerice
        rand_curent.extend(valori)
        while len(rand_curent) >= len(cerere_magazine):  # Construim rânduri complete
            costuri_livrare.append(rand_curent[:len(cerere_magazine)])
            rand_curent = rand_curent[len(cerere_magazine):]

    numar_depozite = len(capacitate_depozite)
    numar_magazine = len(cerere_magazine)

    # Citirea costurilor fixe pentru magazine (Fjk)
    linii_fixe = []
    start_fixe = False
    for linie in linii:
        linie = linie.strip()
        if linie.startswith('Fjk = [['):  # Începutul matricei Fjk
            start_fixe = True
            linii_fixe.append(linie)
        elif start_fixe:
            linii_fixe.append(linie)
            if linie.endswith(']];'):  # Sfârșitul matricei
                break

    # Procesare matrice Fjk
    rand_curent = []
    for linie in linii_fixe:
        valori = list(map(int, re.findall(r'\d+', linie)))
        rand_curent.extend(valori)
        while len(rand_curent) >= len(cerere_magazine):
            costuri_fixe_magazine.append(rand_curent[:len(cerere_magazine)])
            rand_curent = rand_curent[len(cerere_magazine):]

    # Returnăm datele citite
    return numar_depozite, numar_magazine, capacitate_depozite, cerere_magazine, costuri_livrare, costuri_fixe_magazine


def prob_transport(d, r, SCj, Dk, Cjk, Fjk):
    """
    Calculează soluția optimă pentru problema de transport minimizând costurile.
    d: Numărul de depozite.
    r: Numărul de magazine.
    SCj: Lista capacităților depozitelor.
    Dk: Lista cererilor magazinelor.
    Cjk: Matricea costurilor de livrare între depozite și magazine.
    Fjk: Matricea costurilor fixe pentru activarea magazinelor.
    return: Costul total, soluția de transport, capacitățile și cererile rămase, și numărul de pași.
    """
    # Copiem matricea costurilor de livrare pentru modificări
    costuri_livrare_copie = [rand[:] for rand in Cjk]
    # Inițializăm matricea soluției de transport
    solutie_transport = np.zeros((d, r), dtype=int)
    cost_total = 0  # Costul total
    magazine_active = set()  # Magazine deja activate (pentru costurile fixe)

    # Parcurgem fiecare depozit
    for depozit in range(d):
        # Continuăm până când depozitul are capacitate și există cerere
        while SCj[depozit] > 0 and sum(Dk) > 0:
            # Calculăm costurile efective pentru fiecare magazin
            costuri_meta = [
                costuri_livrare_copie[depozit][magazin] + (Fjk[depozit][magazin] if magazin not in magazine_active else 0)
                for magazin in range(r)
            ]
            minim = min(costuri_meta)  # Alegem costul minim

            if minim == float('inf'):  # Dacă nu există costuri disponibile, ieșim
                break

            # Determinăm magazinul cu cost minim
            magazin_minim = costuri_meta.index(minim)
            # Calculăm cantitatea transportată
            cantitate_transportata = min(SCj[depozit], Dk[magazin_minim])

            # Actualizăm soluția și starea depozitului/magazinului
            solutie_transport[depozit][magazin_minim] = cantitate_transportata
            SCj[depozit] -= cantitate_transportata
            Dk[magazin_minim] -= cantitate_transportata

            # Adăugăm magazinul la lista activă dacă nu este deja
            if magazin_minim not in magazine_active:
                magazine_active.add(magazin_minim)

            # Actualizăm costul total
            cost_total += cantitate_transportata * Cjk[depozit][magazin_minim]
            if magazin_minim not in magazine_active:
                cost_total += Fjk[depozit][magazin_minim]

            # Dacă magazinul este complet deservit, eliminăm din matricea costurilor
            if Dk[magazin_minim] == 0:
                costuri_livrare_copie[depozit][magazin_minim] = float('inf')

    return cost_total, solutie_transport.astype(int).tolist(), SCj, Dk


def procesare_date(folder_intrare, fisier_iesire_csv):
    """
    Procesează fișierele dintr-un folder și calculează costurile minime pentru fiecare instanță.
    folder_intrare: Calea către folderul cu fișierele de intrare.
    fisier_iesire_csv: Calea pentru fișierul de ieșire CSV.
    """
    rezultate_csv = []  # Lista pentru rezultatele procesate

    # Parcurgem toate instanțele definite
    for tip in ["small", "medium", "large"]:
        for numar in range(1, 26):
            # Generăm numele fișierului și calea completă
            nume_fisier = f"Lab01_FCR_{tip}_{numar:02d}.dat"
            cale_fisier = os.path.join(folder_intrare, nume_fisier)
            # Verificăm dacă fișierul există
            if os.path.exists(cale_fisier):
                # Citim datele din fișier
                d, r, SCj, Dk, Cjk, Fjk = citire(cale_fisier)
                # Calculăm soluția minimă
                cost_total, solutie_transport, SCj_ramas, Dk_ramas = prob_transport(d, r, SCj, Dk, Cjk, Fjk)
                # Adăugăm rezultatul la lista pentru CSV
                rezultate_csv.append([f"{tip}_instance_{numar:02d}", cost_total])

    # Salvăm rezultatele în fișierul CSV
    with open(fisier_iesire_csv, 'w', newline='') as fisier:
        writer = csv.writer(fisier)
        writer.writerow(['Instanță', 'Cost Total'])  # Header pentru CSV
        writer.writerows(rezultate_csv)  # Scriem rândurile rezultate


if __name__ == "__main__":
    # Directorul cu fișierele de intrare și fișierul de ieșire
    folder_intrare = "Lab_FCR_instances"
    fisier_iesire_csv = "rezultate_cost_fix_magazin.csv"
    # Procesăm datele și generăm fișierul de ieșire
    procesare_date(folder_intrare, fisier_iesire_csv)
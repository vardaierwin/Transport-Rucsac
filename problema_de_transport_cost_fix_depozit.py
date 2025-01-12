import os
import csv
import numpy as np
import heapq
import re

def citire(cale_fisier):
    """
    Citește datele din fișierul de intrare.
    """
    with open(cale_fisier, 'r') as file:
        lines = file.readlines()

    SCj = []
    Fj = []
    Dk = []
    Cjk = []

    for line in lines:
        line = line.strip()
        if line.startswith('SCj'):
            SCj = list(map(int, re.findall(r'\d+', line)))
        elif line.startswith('Fj'):
            Fj = list(map(int, re.findall(r'\d+', line)))  # Citim Fj
        elif line.startswith('Dk'):
            Dk = list(map(int, re.findall(r'\d+', line)))

    cjk_lines = []
    start_cjk = False
    for line in lines:
        line = line.strip()
        if line.startswith('Cjk = [['):
            start_cjk = True
            cjk_lines.append(line)
        elif start_cjk:
            cjk_lines.append(line)
            if line.endswith(']];'):
                break

    current_row = []
    for line in cjk_lines:
        numbers = list(map(int, re.findall(r'\d+', line)))
        current_row.extend(numbers)
        while len(current_row) >= len(Dk):
            Cjk.append(current_row[:len(Dk)])
            current_row = current_row[len(Dk):]

    d = len(SCj)
    r = len(Dk)

    return d, r, SCj, Fj, Dk, Cjk

def prob_transport(d, r, SCj, Dk, Cjk, Fj):
    """
    Rezolvă problema de transport folosind metoda Vogel.
    """
    copie_Cjk = [row[:] for row in Cjk]  # Copie a matricei costurilor
    solutie_transport = np.zeros((d, r), dtype=int)  # Matricea soluției
    total_cost = 0  # Cost total

    # Liste pentru a marca depozitele și piețele completate
    complet_rând = [False] * d
    complet_coloană = [False] * r

    # Inițializăm heap-urile pentru penalitățile de rând și coloană
    penalitati_rând = []
    penalitati_coloană = []

    # Funcție pentru a calcula penalitatea
    def calc_penalitate_minim(costuri, complet):
        if complet:
            return 0
        valori = sorted([c for c in costuri if c != float('inf')])
        if len(valori) >= 2:
            return valori[1] - valori[0]
        elif len(valori) == 1:
            return valori[0]
        return 0

    # Calculăm penalitățile inițiale
    for i in range(d):
        if not complet_rând[i]:
            penalitati_rând.append(
                (calc_penalitate_minim(Cjk[i], complet_rând[i]), i))
    for j in range(r):
        if not complet_coloană[j]:
            penalitati_coloană.append((calc_penalitate_minim(
                [Cjk[i][j] for i in range(d)], complet_coloană[j]), j))

    # Transformăm listele în heap-uri
    heapq.heapify(penalitati_rând)
    heapq.heapify(penalitati_coloană)

    while sum(SCj) > 0 and sum(Dk) > 0:        

        # Alegem rândul și coloana cu penalitățile maxime, dar doar dacă sunt valide
        if penalitati_rând and (not penalitati_coloană or penalitati_rând[0][0] >= penalitati_coloană[0][0]):
            penalitate_maximă, row = heapq.heappop(penalitati_rând)
            if SCj[row] == 0:  # Dacă depozitul este complet epuizat, trecem mai departe
                continue
            col = Cjk[row].index(min(Cjk[row]))
        else:
            penalitate_maximă, col = heapq.heappop(penalitati_coloană)
            if Dk[col] == 0:  # Dacă piața este complet epuizată, trecem mai departe
                continue
            row = min((Cjk[i][col], i)
                      for i in range(d) if not complet_rând[i])[1]

        # Verificăm dacă există capacitate disponibilă și cerință rămasă
        if SCj[row] > 0 and Dk[col] > 0:
            cost = min(SCj[row], Dk[col])
            solutie_transport[row][col] = cost
            SCj[row] -= cost
            Dk[col] -= cost

            if SCj[row] == 0:
                complet_rând[row] = True
            if Dk[col] == 0:
                complet_coloană[col] = True

            # Actualizarea costului total
            total_cost += cost * copie_Cjk[row][col]

            # Actualizăm penalitățile pe rânduri și coloane
            if not complet_rând[row]:
                penalitati_rând.append(
                    (calc_penalitate_minim(Cjk[row], complet_rând[row]), row))
                heapq.heapify(penalitati_rând)
            if not complet_coloană[col]:
                penalitati_coloană.append((calc_penalitate_minim(
                    [Cjk[i][col] for i in range(d)], complet_coloană[col]), col))
                heapq.heapify(penalitati_coloană)

    Fj = SCj  # Cantitatea rămasă în depozit
    # Matricea soluției de transport
    Xjk = solutie_transport.astype(int).tolist()
    # Cantitatea totală livrată către fiecare piață
    Uj = [sum(Xjk[i][j] for i in range(d)) for j in range(r)]

    return Fj, Xjk, Uj, Dk, total_cost

def procesare_date(folder_intrare, fisier_iesire_csv):
    """
    Procesează datele din folderul de intrare și salvează rezultatele în fișierul CSV.
    """
    rezultate_csv = []

    if not os.path.exists(folder_intrare):
        print(f"Eroare: Folderul de intrare '{folder_intrare}' nu exista.")
        return

    for tip in ["small", "medium", "large"]:
        for num in range(1, 26):
            nume_fisier = f"Lab01_FCD_{tip}_{num:02d}.dat"
            cale_fisier = os.path.join(folder_intrare, nume_fisier)

            if not os.path.isfile(cale_fisier):
                continue

            # Citim datele din fișier
            d, r, SCj, Fj, Dk, Cjk = citire(cale_fisier)

            # Aplicăm metoda Vogel
            Fj, Xjk, Uj, Dk_final, cost_total = prob_transport(
                d, r, SCj, Dk, Cjk, Fj)
            # Salvăm rezultatele în format CSV
            rezultate_csv.append([f"{tip}_instance_{num:02d}", cost_total])
            
    # Salvăm rezultatele în fișierul CSV
    header = ['Instanta', 'Cost Total']
    with open(fisier_iesire_csv, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rezultate_csv)

# Exemplu de utilizare a funcției
if __name__ == "__main__":
    folder_intrare = "Lab_FCD_instances"
    fisier_iesire_csv = "rezultate_cost_fix_depozit.csv"
    procesare_date(folder_intrare, fisier_iesire_csv)
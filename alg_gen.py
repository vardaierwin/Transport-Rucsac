import random

# Functia care evalueaza cromozomul: calculeaza scorul si greutatea totala
def evalueaza_cromozom(cromozom, valori, greutati, capacitate_maxima):
    scor = 0
    greutate_totala = 0
    # Parcurgem fiecare bit din cromozom
    for i in range(len(cromozom)):
        # Dacă bitul este '1', adăugăm valoarea și greutatea asociate
        if cromozom[i] == '1':
            # Verificăm dacă adăugarea greutății depășește capacitatea maximă
            if greutate_totala + greutati[i] > capacitate_maxima:
                break  # Oprim adăugarea dacă depășește capacitatea
            scor += valori[i]  # Adăugăm valoarea obiectului
            greutate_totala += greutati[i]  # Adăugăm greutatea obiectului
    return scor, greutate_totala

# Functia care gaseste cel mai bun cromozom dintr-o populatie
def gaseste_solutie_optimala(populatie, valori, greutati, capacitate_maxima):
    # Creăm o listă de scoruri pentru fiecare cromozom din populație
    scoruri = [
        {
            "cromozom": cromozom,
            "scor": evalueaza_cromozom(cromozom, valori, greutati, capacitate_maxima)[0],
            "greutate": evalueaza_cromozom(cromozom, valori, greutati, capacitate_maxima)[1],
        }
        for cromozom in populatie
    ]
    # Sortăm lista de scoruri descrescător după scor
    scoruri.sort(key=lambda x: x["scor"], reverse=True)
    return scoruri[0]  # Returnăm cel mai bun cromozom

# Functia care genereaza o populatie initiala
def genereaza_populatie(numar_indivizi, lungime_cromozom):
    populatie = []
    # Creăm o populație aleatorie de cromozomi
    for _ in range(numar_indivizi):
        cromozom = ''.join([str(random.choice([0, 1])) for _ in range(lungime_cromozom)])
        populatie.append(cromozom)  # Adăugăm cromozomul la populație
    return populatie

# Functia de selectie a indivizilor care au cel mai mare scor si care sunt valizi (nu depasesc capacitatea)
def selecteaza_indivizi_valizi(populatie, valori, greutati, capacitate_maxima, procentaj):
    # Creăm o listă de scoruri pentru fiecare individ din populație
    scoruri = [(individ, *evalueaza_cromozom(individ, valori, greutati, capacitate_maxima)) for individ in populatie]
    # Filtrăm doar indivizii care sunt valizi (nu depășesc capacitatea maximă)
    scoruri = [fs for fs in scoruri if fs[2] <= capacitate_maxima]
    if not scoruri:
        print("Eroare: Nu exista cromozomi validi.")
        return []  # Dacă nu există cromozomi valizi, returnăm o listă goală
    # Sortăm indivizii valizi după scor, descrescător
    scoruri.sort(key=lambda x: x[1], reverse=True)
    # Selectăm procentajul cel mai mare dintre indivizii valizi
    numar_indivizi_selectati = int(len(scoruri) * procentaj)
    return [individ for individ, _, _ in scoruri[:numar_indivizi_selectati]]  # Returnăm indivizii selectați

# Functia care realizeaza combinarea a doi parinti intr-un descendent
def combinare(cut_point, parinti):
    # Verificăm validitatea punctului de tăiere
    if cut_point < 0 or cut_point >= len(parinti[0]):
        print("Punct de taiere invalid.")
        return []  # Dacă punctul de tăiere nu este valid, returnăm o listă goală
    # Creăm doi descendenți prin combinarea celor doi părinți la punctul de tăiere
    descendent1 = parinti[0][:cut_point] + parinti[1][cut_point:]
    descendent2 = parinti[1][:cut_point] + parinti[0][cut_point:]
    return [descendent1, descendent2]  # Returnăm cei doi descendenți

# Functia care aplica combinarea pentru o lista de parinti
def aplica_combinație(parinti, valori, greutati, capacitate_maxima, rata_combinație):
    numar_combinatii = int(len(parinti) * rata_combinație)
    descendenti = []

    # Realizăm combinații pentru fiecare pereche de părinți
    for _ in range(numar_combinatii // 2):
        grup1 = random.sample(parinti, 3)
        grup1.sort(key=lambda x: evalueaza_cromozom(x, valori, greutati, capacitate_maxima)[0], reverse=True)
        parinte1 = grup1[0]

        grup2 = random.sample(parinti, 3)
        grup2.sort(key=lambda x: evalueaza_cromozom(x, valori, greutati, capacitate_maxima)[0], reverse=True)
        parinte2 = grup2[0]

        punct_taiere = random.randint(1, len(parinti[0]) - 1)  # Alegem un punct de tăiere aleator
        descendenti += combinare(punct_taiere, [parinte1, parinte2])  # Generăm și adăugăm descendenții

    return descendenti  # Returnăm lista de descendenți

# Functia care aplica mutatii asupra populatiei
def aplica_mutatii(parinti, rata_modificare):
    numar_modificari = int(len(parinti) * rata_modificare)
    # Aplicăm mutații aleatorii pe indivizii din populație
    for _ in range(numar_modificari):
        individ = random.choice(parinti)  # Alegem un individ aleator
        punct_modificare = random.randint(0, len(individ) - 1)  # Alegem un punct de modificare aleator
        cromozom_modificat = list(individ)  # Transformăm cromozomul într-o listă
        cromozom_modificat[punct_modificare] = '1' if cromozom_modificat[punct_modificare] == '0' else '0'  # Mutăm bitul
        parinti.append(''.join(cromozom_modificat))  # Adăugăm cromozomul modificat la populație
    return parinti  # Returnăm populația modificată

# Functia care optimizeaza mutatiile si asigura ca cromozomii respecta capacitatea maxima a rucsacului
def optimizeaza_mutatii(descendenti, valori, greutati, capacitate_maxima):
    cromozomi_validi = []

    # Verificăm dacă mutațiile respectă capacitatea maximă a rucsacului
    for cromozom in descendenti:
        scor, greutate = evalueaza_cromozom(cromozom, valori, greutati, capacitate_maxima)

        # Dacă greutatea depășește capacitatea, modificăm cromozomul
        while greutate > capacitate_maxima:
            index_mutatie = random.choice([i for i in range(len(cromozom)) if cromozom[i] == '1'])
            cromozom = cromozom[:index_mutatie] + '0' + cromozom[index_mutatie + 1:]  # Îndepărtăm obiectul
            scor, greutate = evalueaza_cromozom(cromozom, valori, greutati, capacitate_maxima)  # Recaclulăm scorul

        cromozomi_validi.append(cromozom)  # Adăugăm cromozomul valid la listă

    return cromozomi_validi  # Returnăm lista de cromozomi validați

# Programul principal
if __name__ == "__main__":
    # Parametrii problemei rucsacului
    capacitate_maxima = 50
    valori = [110, 110, 5, 6, 70, 5, 83, 66, 50, 40]
    greutati = [3, 5, 6, 12, 7, 2, 6, 9, 8, 17]

    numar_indivizi = 3000
    lungime_cromozom = len(valori)
    procentaj_elitism = 0.10
    procentaj_combinație = 0.85
    procentaj_modificare = 0.05
    numar_generatii = 300  # Numărul de generații

    # Crearea populatiei initiale
    populatie = genereaza_populatie(numar_indivizi, lungime_cromozom)

    # Algoritmul genetic
    for generatie in range(numar_generatii):
        print(f"Generația {generatie + 1}")

        # Selectarea celor mai buni indivizi
        indivizi_selectati = selecteaza_indivizi_valizi(populatie, valori, greutati, capacitate_maxima, procentaj_elitism)

        # Aplicarea combinării
        descendenti = aplica_combinație(indivizi_selectati, valori, greutati, capacitate_maxima, procentaj_combinație)

        # Aplicarea mutațiilor
        populatie_noua = aplica_mutatii(descendenti, procentaj_modificare)

        # Optimizarea mutațiilor
        populatie_finala = optimizeaza_mutatii(populatie_noua, valori, greutati, capacitate_maxima)

        # Găsirea soluției optime
        solutie_optima = gaseste_solutie_optimala(populatie_finala, valori, greutati, capacitate_maxima)
        print(f"Cromozom: {solutie_optima['cromozom']}, Scor: {solutie_optima['scor']}, Greutate: {solutie_optima['greutate']} din {capacitate_maxima}")
from pathlib import Path
import math
import pandas as pd
import ollama

MODEL_EMBEDDING = "bge-m3:latest"
MODEL_JEZIKA = "jobautomation/OpenEuroLLM-Croatian:latest"

GLAVNA_MAPA = Path(__file__).resolve().parent
PUTANJA_CSV = GLAVNA_MAPA / "podaci" / "podaci_knjiznica.csv"
PUTANJA_TXT = GLAVNA_MAPA / "podaci" / "pravila_knjiznice.txt"

dokumenti = []
vektori = []
baza_ucitana = False


def ocisti(vrijednost):
    if pd.isna(vrijednost):
        return ""

    return str(vrijednost).strip()


def dohvati(red, nazivi):
    for naziv in nazivi:
        if naziv in red:
            return ocisti(red[naziv])

    return ""


def napravi_embedding(tekst):
    odgovor = ollama.embed(
        model=MODEL_EMBEDDING,
        input=tekst
    )

    if hasattr(odgovor, "embeddings"):
        return odgovor.embeddings[0]

    return odgovor["embeddings"][0]


def izracunaj_slicnost(vektor1, vektor2):
    umnozak = 0
    zbroj1 = 0
    zbroj2 = 0

    for i in range(len(vektor1)):
        umnozak += vektor1[i] * vektor2[i]
        zbroj1 += vektor1[i] * vektor1[i]
        zbroj2 += vektor2[i] * vektor2[i]

    if zbroj1 == 0 or zbroj2 == 0:
        return 0

    return umnozak / (math.sqrt(zbroj1) * math.sqrt(zbroj2))


def ucitaj_knjige():
    tablica = pd.read_csv(PUTANJA_CSV, sep=";", encoding="utf-8-sig")
    tablica.columns = [str(stupac).strip() for stupac in tablica.columns]

    knjige = []

    for _, red in tablica.iterrows():
        naslov = dohvati(red, ["Naslov", "naslov"])
        autor = dohvati(red, ["Autor", "autor"])
        godina = dohvati(red, ["Godina", "godina"])
        zanr = dohvati(red, ["Žanr", "Zanr", "žanr", "zanr"])
        kategorija = dohvati(red, ["Kategorija", "kategorija"])
        opis = dohvati(red, ["Opis", "opis"])
        dostupnost = dohvati(red, ["Dostupnost", "dostupnost"])
        lokacija = dohvati(red, ["Lokacija", "lokacija"])
        kljucne_rijeci = dohvati(red, [
            "Ključne riječi",
            "Kljucne rijeci",
            "Ključne_riječi",
            "kljucne_rijeci"
        ])

        tekst = f"""
KNJIGA
Naslov: {naslov}
Autor: {autor}
Godina: {godina}
Žanr: {zanr}
Kategorija: {kategorija}
Opis: {opis}
Dostupnost: {dostupnost}
Lokacija: {lokacija}
Ključne riječi: {kljucne_rijeci}
""".strip()

        knjige.append({
            "tekst": tekst,
            "izvor": "Knjiga: " + naslov
        })

    return knjige


def ucitaj_pravila():
    tekst = PUTANJA_TXT.read_text(encoding="utf-8")
    dijelovi = tekst.split("\n\n")

    pravila = []

    for dio in dijelovi:
        dio = dio.strip()

        if dio != "":
            pravila.append({
                "tekst": "PRAVILO KNJIŽNICE\n" + dio,
                "izvor": "Pravila knjižnice"
            })

    return pravila


def ucitaj_bazu():
    global baza_ucitana

    if baza_ucitana:
        return

    svi_dokumenti = ucitaj_knjige() + ucitaj_pravila()

    for dokument in svi_dokumenti:
        dokumenti.append(dokument)
        vektori.append(napravi_embedding(dokument["tekst"]))

    baza_ucitana = True


def bonus_za_podudaranje(pitanje, tekst):
    pitanje = pitanje.lower()
    tekst = tekst.lower()
    bonus = 0

    rijeci = pitanje.split()

    for rijec in rijeci:
        rijec = rijec.strip(".,!?;:'\"()[]{}")

        if len(rijec) >= 4 and rijec in tekst:
            bonus += 0.03

    if bonus > 0.20:
        bonus = 0.20

    return bonus


def pronadi_relevantne_podatke(pitanje):
    ucitaj_bazu()

    vektor_pitanja = napravi_embedding(pitanje)
    rezultati = []

    for i in range(len(dokumenti)):
        slicnost = izracunaj_slicnost(vektor_pitanja, vektori[i])
        bonus = bonus_za_podudaranje(pitanje, dokumenti[i]["tekst"])

        rezultat = {
            "tekst": dokumenti[i]["tekst"],
            "izvor": dokumenti[i]["izvor"],
            "slicnost": slicnost + bonus
        }

        rezultati.append(rezultat)

    rezultati.sort(key=lambda podatak: podatak["slicnost"], reverse=True)

    return rezultati[:5]


def ocisti_odgovor(tekst):
    tekst = tekst.replace("**", "")
    tekst = tekst.replace("###", "")

    nove_linije = []

    for linija in tekst.split("\n"):
        linija = linija.strip()

        if linija.startswith("*"):
            linija = "- " + linija.lstrip("*").strip()

        linija = linija.replace("*", "")
        nove_linije.append(linija)

    return "\n".join(nove_linije).strip()


def generiraj_odgovor(pitanje, relevantni_podaci):
    kontekst = ""

    for podatak in relevantni_podaci:
        kontekst += podatak["tekst"] + "\n\n---\n\n"

    prompt = f"""
Ti si BookBot, AI asistent knjižnice.

Odgovaraj na hrvatskom jeziku.
Koristi samo informacije iz konteksta.
Nemoj izmišljati knjige, autore, dostupnost, lokacije ni pravila.
Ako odgovor ne postoji u kontekstu, reci: "Hmm, tu informaciju trenutno nemam u bazi knjižnice."

Nemoj uvijek prepisivati sve podatke iz CSV-a.
Prvo prepoznaj što korisnik pita, pa prilagodi odgovor.

Ako korisnik pita o čemu se radi knjiga:
- napiši kratak prirodan odlomak od 2 do 4 rečenice
- koristi opis knjige iz konteksta
- nemoj navoditi lokaciju i dostupnost ako korisnik to nije tražio

Ako korisnik pita je li knjiga dostupna ili gdje se nalazi:
- napiši dostupnost i lokaciju
- odgovor neka bude kratak

Ako korisnik traži preporuku:
- odgovori u natuknicama
- napiši naslov i kratko objašnjenje zašto je knjiga dobra preporuka
- dodaj dostupnost i lokaciju ako postoje

Ako korisnik pita za pravila knjižnice:
- odgovori kratko i jasno

Ako korisnik postavi subjektivno pitanje, primjerice koja je knjiga najbolja, najgora ili koje je pravilo najgluplje:
- nemoj izmišljati subjektivne ocjene
- reci da baza knjižnice ne sadrži subjektivne ocjene
- ako možeš, ponudi neutralan odgovor na temelju dostupnih podataka

Stil odgovora:
- budi prijateljski i koristan
- koristi emoji povremeno, ali nemoj pretjerivati
- ne koristi markdown formatiranje
- ne koristi znak zvjezdice
- ne podebljavaj naslove knjiga
- ako nabrajaš knjige, koristi običnu crticu umjesto zvjezdice

KONTEKST:
{kontekst}

PITANJE:
{pitanje}

ODGOVOR:
""".strip()

    odgovor = ollama.generate(
        model=MODEL_JEZIKA,
        prompt=prompt
    )

    if hasattr(odgovor, "response"):
        tekst_odgovora = odgovor.response.strip()
    else:
        tekst_odgovora = odgovor["response"].strip()

    return ocisti_odgovor(tekst_odgovora)


def pitaj_chatbota(pitanje):
    relevantni_podaci = pronadi_relevantne_podatke(pitanje)
    odgovor = generiraj_odgovor(pitanje, relevantni_podaci)

    return {
        "answer": odgovor,
        "sources": []
    }
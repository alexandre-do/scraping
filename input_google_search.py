import pandas as pd
import os
import typer

ENTITY = ["RTE", '"Réseau de transport d\'electricité"', "INEO"]
PROJECT = [
    '"Ligne Ponteau-réaltor de 400 KV"',
    '"Golfe de Gascogne"',
    '"Linge à très Haute tension d\'Avelin à Gavrelle"',
    '"parc éolien offshore"',
]
METIER = [
    "électrique",
    "puissance électrique",
    "champs électromangétiques",
    "champs magnétiques",
    "courant alternatif",
    "haute tension",
    "très haute tension",
    "400 KV",
    "400 000 volts",
    "terrestre",
    "sous terrain",
    "aérien",
    "installation",
    "construction",
    "implémentation",
    "déviation",
]
OUVRAGE = [
    '"centrale nucléaire"',
    '"central carbon"',
    '"parc éolien"',
    "ligne",
    "cable",
    '"interconnexion électrique"',
    "passage",
    "tracé",
    "pylone",
    '"double circuit"',
    '"poste électrique"',
    "transformateur",
    "barrage",
]
CAUSE = [
    "environnement",
    '"bio diversité"',
    '"biodiversité"',
    '"transition écologique"',
    "santé",
    '"cadre de vie"',
    "sanitaire",
    "paysage",
    '"monuments historiques"',
    "incidents",
    "crèches",
    "écoles",
    "polution visuelle",
    "ondes",
    "éloctrosensibilité",
    "expropriation",
    "éoliennes",
]
OPP_FAIBLE = [
    "opposition",
    "interrogation",
    "inquiétude",
    '"étude d\'impact"',
    "exposition",
    '"travaux interminables"',
    "investigation",
    '"réunion d\'informations"',
    '"permanence d\'informations"',
    '"déni de démocratie"',
]
OPP_MOYENNE = [
    '"association de riverains"',
    '"réunion de concertation"',
    "pétition",
    "collectif",
    "mobilisation",
    '"comité de défense et de soutien"',
    "contestation",
    "négociation",
    '"démarche citoyenne"',
    "constestation",
]
OPP_FORTE = [
    "manifestation",
    "rassemblement",
    "enquête",
    "dénoncement",
    "prédateur",
    "huissier",
    "justice",
    "préfet",
    "hostilité",
]
OPP_ORG = ["Greenpeace", '"Extinction rebellion"']
PATH_SAVE = "./inputs/"
SAVED_FILE_NAME = "input_google_search.txt"
if __name__ == "__main__":
    date_from = ["2018/01/01", "2019/01/01", "2020/01/01"]
    date_to = ["2019/01/01", "2020/01/01", "2021/01/01"]
    save_file = ["opp_forte_2018.jsonl", "opp_forte_2019.jsonl", "opp_forte_2020.jsonl"]
    requests = []
    for opp_word in OPP_FORTE:
        for date_from_, date_to_, save_file_ in zip(date_from, date_to, save_file):
            request = ";".join(
                [f'"RTE" {opp_word}', date_from_, date_to_, PATH_SAVE + save_file_]
            )
            requests.append(request)

    if not os.path.isdir(PATH_SAVE):
        os.makedirs(PATH_SAVE)
    with open(PATH_SAVE + SAVED_FILE_NAME, "w") as f:
        for request in requests:
            f.write(request)
            f.write("\n")

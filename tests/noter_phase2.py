"""Vérification de la phase 2, critère par critère — FOURNI, rien à modifier.

Lancez-le directement :

    python3 tests/noter_phase2.py

Trois temps :

  [1/3]  les tests de `test_phase2.py` — un cas par comportement. Tant qu'ils
         ne passent pas tous, inutile d'aller plus loin : ce sont eux qui
         décrivent ce que votre code doit faire.

  [2/3]  les tests `test_critere_3.py` à `test_critere_7.py` — les mêmes
         comportements, sur beaucoup plus de valeurs, un fichier par critère
         de la grille d'évaluation. Chaque critère est noté sur 100 % : ses
         sous-critères comptent à parts égales, et chacun est accordé au
         prorata de ses cas réussis. S'y ajoutent deux contrôles non notés
         (`test_controle_*.py`) : le travail de la phase 1 fonctionne encore.

  [3/3]  le style, vérifié par pylint avec le `pylintrc` du projet.

Ce fichier est un outil de travail : le résultat qu'il affiche n'est pas la
note du travail remis, qui tient aussi compte de la lisibilité du code, des
commentaires et des bonus.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import pathlib
import re
import subprocess
import sys
import textwrap

import pytest

DOSSIER = pathlib.Path(__file__).resolve().parent
RACINE = DOSSIER.parent
LARGEUR = 78

# ------------------------------------------------------------- les critères ---

# un fichier tests/test_critere_N.py par critère : (titre, poids dans la grille)
CRITERES = {
    "TestCritere3PiluleDeForce": ("Critère 3 — Pilules de force et fuite", 20),
    "TestCritere4Collisions": ("Critère 4 — Collisions, vies et fin de partie", 25),
    "TestCritere5Sons": ("Critère 5 — Option --sourdine et sons", 10),
    "TestCritere6Scores": ("Critère 6 — Option --lister-scores et scores", 10),
    "TestCritere7Jauge": ("Critère 7 — Jauge d'accélération", 15),
}

# un fichier tests/test_controle_*.py par contrôle : le travail de la phase 1,
# déjà dans la coquille, doit continuer de fonctionner ; aucun poids
CONTROLES = {
    "TestControleMouvement": "Mouvement de Paxman et des fantômes",
    "TestControleRecolte": "Récolte des récompenses",
}

# les critères 1 et 2 de la grille ne se vérifient pas automatiquement
POIDS_TOTAL = sum(poids for _, poids in CRITERES.values())

# ------------------------------------------------- la lecture des échecs ---

# chaque règle : un motif cherché dans le message d'erreur, et la phrase à
# afficher ; `{0}` reprend ce que le motif a capturé
REGLES = (
    # un message écrit dans le test (assert ..., "message") est le plus parlant
    (r"AssertionError: (?!assert )(.+)$", "{0}"),
    (r"NotImplementedError", "la méthode n'est pas encore écrite"),
    (r"has no attribute '([^']+)'", "l'attribut ou la méthode « {0} » n'existe pas encore"),
    (r"DID NOT RAISE", "la partie aurait dû se terminer (StopIteration), mais elle a continué"),
    (r"StopIteration", "la partie s'est terminée alors qu'elle devait continuer"),
    (r"FileNotFoundError.*scores\.txt", "le fichier scores.txt n'a pas été créé"),
    (r"KeyError: (.+)$", "la clé {0} n'existe pas"),
)


def _apres(lignes: list[str], prefixe: str) -> str | None:
    """Retourne ce qui suit `prefixe` dans la première ligne qui le porte."""

    for ligne in lignes:
        if ligne.startswith(prefixe):
            return ligne[len(prefixe):].strip()

    return None


def _comparaison(obtenu: str, attendu: str) -> str:
    """Met en mots une comparaison ratée."""

    # pytest.approx ajoute sa tolérance (« 12 ± 1.2e-05 ») : inutile ici
    attendu = re.sub(r" ± \S+", "", attendu)

    if obtenu == "None":
        return f"aucune valeur (None) au lieu de {attendu}"

    return f"{obtenu} au lieu de {attendu}"


def _expliquer(trace: str) -> str:
    """Traduit une trace pytest en une phrase utile."""

    lignes = [ligne.strip() for ligne in trace.strip().splitlines() if ligne.strip()]
    if not lignes:
        return "le test a échoué"

    # la première ligne « E ... » porte le message de l'erreur
    premiere = next((ligne for ligne in lignes if ligne.startswith("E ")), lignes[0])
    message = premiere.removeprefix("E").strip()

    if "assert " in message:
        message = message[message.index("assert "):]

    for motif, phrase in REGLES:
        trouve = re.search(motif, message)
        if trouve:
            return phrase.format(*trouve.groups())

    # pytest détaille parfois la comparaison (pytest.approx) ; sinon, on lit
    # directement l'assertion
    obtenu, attendu = _apres(lignes, "Obtained:"), _apres(lignes, "Expected:")
    if obtenu is None or attendu is None:
        assertion = re.match(r"assert (.+?) == (.+)$", message)
        obtenu, attendu = assertion.groups() if assertion else (None, None)

    if obtenu is not None:
        return _comparaison(obtenu, attendu)

    condition = message.removeprefix("assert ")
    if condition in ("False", "not True", "None", "0"):
        return "le comportement attendu n'est pas observé"
    if message.startswith("assert "):
        return f"la condition « {condition} » est fausse"

    return message


def _nom_lisible(nodeid: str) -> str:
    """Transforme `fichier.py::Classe::test_quelque_chose[3]` en « quelque chose »."""

    nom = nodeid.split("::")[-1].partition("[")[0]

    return nom.removeprefix("test_").replace("_", " ")


def _classe_de(nodeid: str) -> str:
    """Extrait le nom de la classe de test d'un identifiant pytest."""

    morceaux = nodeid.split("::")

    return morceaux[1] if len(morceaux) > 2 else ""


# -------------------------------------------------------- le collecteur ---


class Collecteur:
    """Greffon pytest qui note les résultats, critère par critère.

    `resultats[critère][sous-critère]` est la liste des cas, réussis ou non.
    """

    def __init__(self, groupe: str | None = None) -> None:
        # `groupe` range tous les résultats au même endroit : c'est ce qu'on
        # fait pour test_phase2.py, qui n'est pas noté mais seulement compté
        self.groupe = groupe
        self.resultats: dict[str, dict[str, list[bool]]] = {}
        self.intentions: dict[str, str] = {}
        self.points: dict[str, str] = {}
        self.echecs: dict[str, dict] = {}

    def pytest_collection_modifyitems(self, items) -> None:
        """Retient, pour chaque test, son intention et son sous-critère."""

        for item in items:
            docstring = (getattr(item.function, "__doc__", None) or "").strip()
            self.intentions[item.nodeid] = docstring.splitlines()[0] if docstring else ""

            marqueur = item.get_closest_marker("point")
            self.points[item.nodeid] = marqueur.args[0] if marqueur else "autres"

    def pytest_runtest_logreport(self, report) -> None:
        """Note le résultat d'un test, et l'explication s'il a échoué."""

        if report.when != "call" and not (report.when == "setup" and report.failed):
            return

        critere = self.groupe or _classe_de(report.nodeid)
        if not self.groupe and critere not in CRITERES and critere not in CONTROLES:
            return

        point = self.points.get(report.nodeid, "autres")
        self.resultats.setdefault(critere, {}).setdefault(point, []).append(report.passed)

        if not report.passed:
            # on regroupe les cas d'un même test paramétré : cinq durées qui
            # échouent pour la même raison, c'est une seule chose à corriger
            echec = self.echecs.setdefault(
                report.nodeid.partition("[")[0],
                {
                    "nom": _nom_lisible(report.nodeid),
                    "critere": CRITERES.get(critere, ("Contrôle",))[0].split(" — ")[0],
                    "intention": self.intentions.get(report.nodeid, ""),
                    "explications": [],
                },
            )
            echec["explications"].append(_expliquer(report.longreprtext))

    def compter(self) -> tuple[int, int]:
        """Retourne le nombre de cas réussis et le nombre total de cas."""

        tous = [
            resultat
            for points in self.resultats.values()
            for resultats in points.values()
            for resultat in resultats
        ]

        return sum(tous), len(tous)

    def pourcentage(self, critere: str) -> float:
        """Retourne la note d'un critère sur 100 : moyenne de ses sous-critères."""

        points = self.resultats.get(critere, {})
        if not points:
            return 0.0

        taux = [sum(resultats) / len(resultats) for resultats in points.values()]

        return 100 * sum(taux) / len(taux)


def _executer(fichiers: list[str], collecteur: Collecteur) -> None:
    """Exécute des fichiers de tests sans rien afficher, en notant les résultats."""

    with contextlib.redirect_stdout(io.StringIO()):
        pytest.main(
            [*(str(DOSSIER / f) for f in fichiers), "-q", "--tb=line", "-p", "no:cacheprovider"],
            plugins=[collecteur],
        )


# ------------------------------------------------------------ l'affichage ---


def _titre(texte: str) -> None:
    print()
    print(texte)
    print("─" * LARGEUR)


def _aligner(etiquette: str, texte: str) -> str:
    """Met « attendu : ... » en forme, replié sur la largeur du rapport."""

    marge = " " * 7

    # les espaces fines insécables (« ») ne doivent pas servir de coupure
    texte = " ".join(texte.split(" ")).replace("\u202f", "\x00")

    return textwrap.fill(
        texte,
        width=LARGEUR,
        initial_indent=f"{marge}{etiquette:<7} : ",
        subsequent_indent=marge + " " * 10,
        break_on_hyphens=False,
    ).replace("\x00", "\u202f")


def _contrat_minimal() -> None:
    """Exécute d'abord `test_phase2.py` et résume ce qu'il reste à écrire."""

    _titre("[1/3]  Les tests de test_phase2.py — un cas par comportement")

    collecteur = Collecteur(groupe="contrat")
    _executer(["test_phase2.py"], collecteur)
    reussis, total = collecteur.compter()

    if total == 0:
        print("  test_phase2.py est introuvable : passons directement aux tests étendus.")
        return

    print(f"  {reussis} / {total} comportements conformes")

    if collecteur.echecs:
        echecs = list(collecteur.echecs.values())
        print()
        print("  Il reste des comportements à écrire :")
        for echec in echecs[:10]:
            print(f"    ·  {echec['intention'] or echec['nom']}")
        if len(echecs) > 10:
            print(f"    …  et {len(echecs) - 10} autres.")
        print()
        print("  Les tests étendus ci-dessous iront donc forcément moins bien.")


def _rapport_des_echecs(collecteur: Collecteur, maximum: int = 12) -> None:
    """Affiche, pour chaque test raté, ce qui était attendu et ce qui s'est passé."""

    echecs = list(collecteur.echecs.values())
    if not echecs:
        return

    _titre("Ce qui ne passe pas encore")

    for echec in echecs[:maximum]:
        explications = echec["explications"]
        cas = f"  ({len(explications)} cas)" if len(explications) > 1 else ""

        print(f"  ✗  {echec['critere']} · {echec['nom']}{cas}")
        if echec["intention"]:
            print(_aligner("attendu", echec["intention"]))
        print(_aligner("obtenu", explications[0]))
        print()

    if len(echecs) > maximum:
        print(f"  …  et {len(echecs) - maximum} autres tests, "
              "qui apparaîtront ici au fur et à mesure.")
        print()


def _bulletin(collecteur: Collecteur) -> float:
    """Affiche chaque critère sur 100 %, détaillé par sous-critère.

    Retourne l'équivalent pondéré, sur POIDS_TOTAL.
    """

    _titre("Résultats par critère (chacun sur 100 %)")

    pondere = 0.0
    for critere, (titre, poids) in CRITERES.items():
        pourcentage = collecteur.pourcentage(critere)
        pondere += poids * pourcentage / 100

        print()
        print(f"  {titre:<64}{pourcentage:>5.0f} %")

        for point, resultats in collecteur.resultats.get(critere, {}).items():
            reussis, total = sum(resultats), len(resultats)
            symbole = "✓" if reussis == total else "✗" if reussis == 0 else "~"
            print(f"     {symbole}  {point:<58}{reussis:>3}/{total}")

    print()
    print("─" * LARGEUR)
    print(f"  {'Équivalent pondéré (poids de la grille, critères 3 à 7)':<62}"
          f"{pondere:>5.1f} / {POIDS_TOTAL}")

    _controles(collecteur)

    return pondere


def _controles(collecteur: Collecteur) -> None:
    """Affiche les contrôles de la phase 1 : réussis ou non, sans note."""

    _titre("Contrôles — le travail de la phase 1 fonctionne encore (non noté)")

    for controle, titre in CONTROLES.items():
        resultats = [r for rs in collecteur.resultats.get(controle, {}).values() for r in rs]
        reussis, total = sum(resultats), len(resultats)
        etat = "intact" if reussis == total else "CASSÉ : à réparer avant tout le reste"
        print(f"  {'✓' if reussis == total else '✗'}  {titre:<44}{reussis:>3}/{total:<4}{etat}")


def _style() -> None:
    """Lance pylint sur tout le projet et affiche tous les messages."""

    _titre("[3/3]  Le style — pylint, avec le pylintrc du projet")

    commande = [
        sys.executable, "-m", "pylint",
        "main.py", "paxman", "tests", "outils"
    ]

    try:
        resultat = subprocess.run(
            commande,
            cwd=RACINE,
            capture_output=True,
            text=True,
            check=False,
            timeout=300
        )
    except (OSError, subprocess.TimeoutExpired) as erreur:
        print(f"  pylint n'a pas pu être lancé ({erreur}).")
        return

    sortie = resultat.stdout + resultat.stderr

    note = re.search(r"rated at (-?[\d.]+)/10", sortie)

    if note is None:
        print(f"  pylint n'est pas installé pour {sys.executable} :")
        print(
            f"      {pathlib.Path(sys.executable).name} "
            "-m pip install -r requirements.txt"
        )
        print(sortie)
        return

    messages = re.findall(
        r"^[CWERF]:\s*\d+,\s*\d+: .*?\(([\w-]+)\)$",
        sortie,
        re.M
    )

    a_faire = messages.count("fixme")
    autres = len(messages) - a_faire

    print(
        f"  {note.group(1)} / 10 — "
        f"{a_faire} TODO restant(s), "
        f"{autres} autre(s) message(s)"
    )

    print()

    if autres == 0 and a_faire == 0:
        print("  Aucun problème détecté par pylint.")
        return

    _titre("Détail des messages Pylint")

    if sortie.strip():
        print(sortie)
    else:
        print("  Aucun message détaillé retourné par pylint.")



def executer_et_noter(avec_pylint: bool = True) -> int:
    """Lance les vérifications et affiche les résultats. Retourne un code de sortie."""

    print()
    print("═" * LARGEUR)
    print("Paxman — phase 2 : vérification de votre travail".center(LARGEUR))
    print("═" * LARGEUR)

    _contrat_minimal()

    _titre("[2/3]  Les tests étendus, critère par critère")

    collecteur = Collecteur()
    fichiers = [*DOSSIER.glob("test_critere_*.py"), *DOSSIER.glob("test_controle_*.py")]
    _executer(sorted(f.name for f in fichiers), collecteur)
    reussis, total = collecteur.compter()
    print(f"  {reussis} / {total} cas réussis")

    _rapport_des_echecs(collecteur)
    pondere = _bulletin(collecteur)

    if avec_pylint:
        _style()

    print()
    if pondere == POIDS_TOTAL:
        print("  Tous les critères sont à 100 %. Relisez votre code, commentez-le,")
        print("  et pensez aux bonus.")
    else:
        print("  Reprenez les sous-critères marqués ✗ ou ~ un par un.")
    print()

    return 0 if pondere == POIDS_TOTAL else 1


if __name__ == "__main__":
    ANALYSEUR = argparse.ArgumentParser(description="Vérifie la phase 2 de Paxman.")
    ANALYSEUR.add_argument("--sans-pylint", action="store_true",
                           help="ne pas lancer pylint (plus rapide)")
    sys.exit(executer_et_noter(avec_pylint=not ANALYSEUR.parse_args().sans_pylint))

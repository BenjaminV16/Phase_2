"""Petites fonctions communes aux tests de la phase 2 — FOURNI, rien à modifier."""

import importlib
import runpy
import sys

import main
from paxman.paxman import Paxman
from paxman.plateau import Plateau
from paxman.recompenses import Pilule, PiluleForce

# des réglages de Paxman, pour les tests qui n'ont pas besoin d'une partie
REGLAGES_PAXMAN = {
    "vies": 3,
    "position-initiale": [14.5, 8],
    "vitesse-défaut": 4.5,
    "vitesse-force": 5.0,
    "accélération-max": 1.4,
    "accélération-montée": 1.5,
    "accélération-descente": 2.5,
    "jauge-vidange": 0.5,
    "jauge-recharge": 0.2,
}


def creer_paxman(**reglages) -> Paxman:
    """Crée un Paxman seul, hors de toute partie, avec ces réglages modifiés.

    Les noms de réglages contiennent des tirets, qui sont interdits dans les
    noms d'arguments ; on écrit donc `jauge_vidange=1.0` pour `jauge-vidange`.
    """

    complets = dict(REGLAGES_PAXMAN)
    complets.update({titre.replace("_", "-"): valeur for titre, valeur in reglages.items()})

    return Paxman(*complets["position-initiale"], reglages=complets)


# un couloir horizontal (rangée 3), avec des ouvertures en haut et en bas
# seulement aux colonnes 2, 4 et 6 :
#
#   j=5   ───────
#   j=4   │.│.│.│
#   j=3   │.....│      Paxman part de (3, 3) vers la droite
#   j=2   │.│.│.│
#   j=1   ───────
COULOIR_HORIZONTAL = [
    "───────",
    "│.│.│.│",
    "│.....│",
    "│.│.│.│",
    "───────",
]


def plateau_en_couloirs(vertical: bool = False) -> Plateau:
    """Retourne le couloir ci-dessus, ou sa transposée (couloir vertical, colonne 3).

    Transposer échange les rôles des flèches : dans le couloir vertical, Paxman
    part de (3, 3) vers le haut et les ouvertures sont à gauche et à droite.
    """

    if not vertical:
        return Plateau(description=COULOIR_HORIZONTAL)

    # la tuile (i, j) du couloir vertical est la tuile (j, i) du couloir horizontal
    hauteur, largeur = len(COULOIR_HORIZONTAL), len(COULOIR_HORIZONTAL[0])

    def symbole_transpose(i, j):
        # le symbole de la tuile (j, i) du couloir horizontal, murs pivotés
        symbole = COULOIR_HORIZONTAL[hauteur - i][j - 1]
        return {"─": "│", "│": "─"}.get(symbole, symbole)

    transpose = [
        "".join(symbole_transpose(i, j) for i in range(1, hauteur + 1))
        for j in range(largeur, 0, -1)
    ]
    return Plateau(description=transpose)


def paxman_lance(vertical: bool = False) -> Paxman:
    """Un Paxman en (3, 3), déjà lancé le long du couloir."""

    paxman = creer_paxman()
    paxman.position = (3.0, 3.0)
    paxman.direction = (0, 1) if vertical else (1, 0)

    return paxman


def tuiles_des_pilules(jeu, classe=Pilule) -> list[tuple[int, int]]:
    """Retourne les tuiles portant une récompense de ce type."""

    return [tuile for tuile, objet in jeu.plateau.items() if isinstance(objet, classe)]


def tuile_de_la_pilule_de_force(jeu) -> tuple[int, int]:
    """Retourne la tuile de la première pilule de force du plateau."""

    tuiles = tuiles_des_pilules(jeu, PiluleForce)
    assert tuiles, "le plateau du niveau 1 devrait contenir des pilules de force"

    return tuiles[0]


def tuile_d_une_pilule_simple(jeu) -> tuple[int, int]:
    """Retourne la tuile d'une pilule ordinaire (pas une pilule de force)."""

    return next(
        tuile for tuile in tuiles_des_pilules(jeu)
        if not isinstance(jeu.plateau.get(tuile), PiluleForce)
    )


def placer_paxman_sur(jeu, tuile: tuple[int, int]) -> None:
    """Pose Paxman exactement sur cette tuile."""

    jeu.paxman.position = (float(tuile[0]), float(tuile[1]))


def vider_le_plateau(jeu, sauf: int = 0) -> None:
    """Ramasse toutes les récompenses, sauf les `sauf` dernières."""

    tuiles = tuiles_des_pilules(jeu)
    for tuile in tuiles[: len(tuiles) - sauf]:
        jeu.plateau.ramasser(tuile)


def rendre_dangereux(jeu) -> None:
    """Sort tous les fantômes du mode « fuite »."""

    for fantome in jeu.fantomes.values():
        fantome.mode = jeu.mode


def analyser(monkeypatch, arguments):
    """Analyse une ligne de commande comme le ferait `python3 main.py ...`."""

    monkeypatch.setattr(sys, "argv", ["main.py", *arguments])

    return main.analyser_ligne_commande()


def executer_main(monkeypatch, arguments) -> tuple[list[dict], int]:
    """Exécute `python3 main.py ...` sans lancer de vraie partie.

    `JeuPaxman` est remplacé par un enregistreur : on retourne la liste des
    parties que main.py a voulu créer (leurs arguments), et le code de sortie.
    """

    parties: list[dict] = []

    class Enregistreur:
        """Prend la place de JeuPaxman et retient comment main.py l'a créé."""

        def __init__(self, **arguments_du_jeu):
            parties.append(arguments_du_jeu)

        def demarrer_boucle_evenements(self):
            """Ne démarre rien : la partie n'est pas jouée."""

    monkeypatch.setattr(importlib.import_module("paxman.jeu"), "JeuPaxman", Enregistreur)
    monkeypatch.setattr(sys, "argv", ["main.py", *arguments])

    try:
        runpy.run_path(main.__file__, run_name="__main__")
    except SystemExit as sortie:
        return parties, sortie.code or 0

    return parties, 0

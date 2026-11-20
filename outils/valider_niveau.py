#!/usr/bin/env python3
"""Valide un fichier de niveau du jeu Paxman.

Ce script ne dépend que de la bibliothèque standard : il peut donc être exécuté
sans avoir installé pyglet.

    python3 valider_niveau.py paxman/niveaux/niveau1.json
    python3 valider_niveau.py mon_niveau.json --carte

Il vérifie notamment que le labyrinthe est *solvable*, c'est-à-dire que toutes
les pilules peuvent être atteintes par Paxman en partant de sa position
initiale.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque

MURS = set("─│┌┐└┘")
PORTES = set("_:")
PILULE = "."
PILULE_FORCE = "o"
VIDE = " "

SYMBOLES_CONNUS = MURS | PORTES | {PILULE, PILULE_FORCE, VIDE}


class Niveau:
    """Vue en lecture seule d'une description de plateau, indicée comme `Plateau`.

    Les tuiles sont indicées à partir de 1, l'origine est en bas à gauche :
    `(i, j)` où `i` est la colonne et `j` la ligne.
    """

    def __init__(self, description: list[str]) -> None:
        self.description = description
        self.hauteur = len(description)
        self.largeur = len(description[0]) if description else 0
        self.grille: dict[tuple[int, int], str] = {}
        for indice_ligne, ligne in enumerate(description):
            j = self.hauteur - indice_ligne
            for i, symbole in enumerate(ligne, 1):
                self.grille[(i, j)] = symbole

    def symbole(self, tuile: tuple[int, int]) -> str:
        """Retourne le symbole dessiné sur cette tuile."""

        return self.grille.get(self.normaliser(tuile), VIDE)

    def normaliser(self, tuile: tuple[int, int]) -> tuple[int, int]:
        """Applique le bouclage des tunnels, comme `Plateau.normaliser_coordonnees`."""

        i, j = tuile
        return ((i - 1) % self.largeur + 1, (j - 1) % self.hauteur + 1)

    def franchissable(self, tuile: tuple[int, int], *, portes_ouvertes: bool) -> bool:
        """Indique si un acteur peut se trouver sur cette tuile."""

        symbole = self.symbole(tuile)
        if symbole in MURS:
            return False
        if symbole in PORTES:
            return portes_ouvertes
        return True

    def voisines(
        self, tuile: tuple[int, int], *, portes_ouvertes: bool
    ) -> list[tuple[int, int]]:
        """Retourne les tuiles franchissables adjacentes à cette tuile."""

        i, j = tuile
        candidates = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
        return [
            self.normaliser(c)
            for c in candidates
            if self.franchissable(c, portes_ouvertes=portes_ouvertes)
        ]

    def accessibles(self, depart: tuple[int, int], *, portes_ouvertes: bool) -> set:
        """Parcours en largeur (BFS) des tuiles atteignables depuis `depart`."""

        depart = self.normaliser(depart)
        vues = {depart}
        file = deque([depart])
        while file:
            tuile = file.popleft()
            for voisine in self.voisines(tuile, portes_ouvertes=portes_ouvertes):
                if voisine not in vues:
                    vues.add(voisine)
                    file.append(voisine)
        return vues

    def recompenses(self) -> set:
        """Retourne l'ensemble des tuiles qui portent une pilule."""

        return {t for t, s in self.grille.items() if s in (PILULE, PILULE_FORCE)}


def tuile_de(position: list[float]) -> tuple[int, int]:
    """Convertit une position du fichier JSON en coordonnées de tuile.

    Utilise `round`, exactement comme `Acteur.tuile_courante`.
    """

    return (round(position[0]), round(position[1]))


class Rapport:
    """Accumule les erreurs et les avertissements trouvés dans un niveau."""

    def __init__(self) -> None:
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def erreur(self, message: str) -> None:
        """Note une erreur : le niveau sera déclaré invalide."""

        self.erreurs.append(message)

    def avertir(self, message: str) -> None:
        """Note un avertissement : le niveau reste valide."""

        self.avertissements.append(message)

    @property
    def valide(self) -> bool:
        """Indique si aucune erreur n'a été trouvée."""

        return not self.erreurs


def lire_le_plateau(config: dict, rapport: Rapport) -> Niveau | None:
    """Vérifie la structure du fichier et la forme du plateau (étapes 1 et 2)."""

    for cle in ("plateau", "paxman", "fantômes", "réglages"):
        if cle not in config:
            rapport.erreur(f"clé {cle!r} absente du fichier de niveau")
    if rapport.erreurs:
        return None

    description = config["plateau"]
    if not description:
        rapport.erreur("le plateau est vide")
        return None

    longueurs = {len(ligne) for ligne in description}
    if len(longueurs) != 1:
        rapport.erreur(
            f"toutes les lignes doivent avoir la même longueur (trouvé : {sorted(longueurs)})"
        )
        return None

    inconnus = set("".join(description)) - SYMBOLES_CONNUS
    if inconnus:
        rapport.erreur(f"symboles inconnus dans le plateau : {sorted(inconnus)}")

    return Niveau(description)


def verifier_les_departs(niveau: Niveau, config: dict, rapport: Rapport) -> None:
    """Vérifie que personne ne démarre dans un mur (étape 3)."""

    depart_paxman = tuile_de(config["paxman"]["position-initiale"])
    if not niveau.franchissable(depart_paxman, portes_ouvertes=False):
        rapport.erreur(
            f"la position initiale de Paxman {depart_paxman} tombe sur un mur ou une porte"
        )

    for reglages in config["fantômes"]:
        depart = tuile_de(reglages["position-initiale"])
        if not niveau.franchissable(depart, portes_ouvertes=True):
            rapport.erreur(
                f"la position initiale de {reglages['nom']} {depart} tombe sur un mur"
            )


def verifier_les_recompenses(niveau: Niveau, depart: tuple[int, int], rapport: Rapport) -> None:
    """Vérifie les pilules, et surtout qu'on puisse toutes les atteindre (étapes 4 et 5)."""

    recompenses = niveau.recompenses()
    pilules_force = {t for t in recompenses if niveau.symbole(t) == PILULE_FORCE}

    if not recompenses:
        rapport.erreur("le plateau ne contient aucune pilule : la partie serait gagnée d'emblée")
    if len(pilules_force) != 4:
        rapport.avertir(
            f"{len(pilules_force)} pilule(s) de force (le niveau original en compte 4)"
        )

    isolees = recompenses - niveau.accessibles(depart, portes_ouvertes=False)
    if isolees:
        rapport.erreur(
            f"{len(isolees)} récompense(s) inatteignable(s) depuis le départ de Paxman, "
            f"par exemple {sorted(isolees)[:5]} : le labyrinthe n'est pas solvable"
        )


def verifier_la_cage(niveau: Niveau, config: dict, rapport: Rapport) -> None:
    """Vérifie que les fantômes peuvent sortir de la cage (étape 6)."""

    depart_paxman = tuile_de(config["paxman"]["position-initiale"])
    for reglages in config["fantômes"]:
        depart = tuile_de(reglages["position-initiale"])
        if depart_paxman not in niveau.accessibles(depart, portes_ouvertes=True):
            rapport.erreur(
                f"{reglages['nom']} ne peut pas rejoindre Paxman : cage sans issue ?"
            )

    cible_cage = tuile_de(config["réglages"]["cible-cage"])
    if not niveau.franchissable(cible_cage, portes_ouvertes=True):
        rapport.erreur(f"le réglage cible-cage {cible_cage} tombe sur un mur")


def juger_la_qualite(niveau: Niveau, depart: tuple[int, int], rapport: Rapport) -> None:
    """Signale ce qui rendrait le labyrinthe peu jouable (étape 7, avertissements)."""

    libres = niveau.accessibles(depart, portes_ouvertes=False)
    culs_de_sac = [
        t for t in libres if len(niveau.voisines(t, portes_ouvertes=False)) == 1
    ]
    if culs_de_sac:
        rapport.avertir(
            f"{len(culs_de_sac)} cul(s)-de-sac, par exemple {sorted(culs_de_sac)[:5]} : "
            "Paxman y sera piégé sans échappatoire"
        )

    if not any(niveau.symbole(tuile) in PORTES for tuile in niveau.grille):
        rapport.avertir("aucune porte de cage sur le plateau")


def valider(config: dict, rapport: Rapport) -> Niveau | None:
    """Vérifie tout le niveau et remplit le rapport. Retourne le niveau lu, ou None."""

    niveau = lire_le_plateau(config, rapport)
    if niveau is None:
        return None

    depart = tuile_de(config["paxman"]["position-initiale"])

    verifier_les_departs(niveau, config, rapport)
    verifier_les_recompenses(niveau, depart, rapport)
    verifier_la_cage(niveau, config, rapport)
    juger_la_qualite(niveau, depart, rapport)

    return niveau


def dessiner_carte(niveau: Niveau, config: dict) -> str:
    """Redessine le plateau en marquant les tuiles inatteignables par un `X`."""

    depart = tuile_de(config["paxman"]["position-initiale"])
    atteignables = niveau.accessibles(depart, portes_ouvertes=False)
    lignes = []
    for indice_ligne, ligne in enumerate(niveau.description):
        j = niveau.hauteur - indice_ligne
        sortie = ""
        for i, symbole in enumerate(ligne, 1):
            if (i, j) == depart:
                sortie += "P"
            elif symbole in (PILULE, PILULE_FORCE) and (i, j) not in atteignables:
                sortie += "X"
            else:
                sortie += symbole
        lignes.append(sortie)
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    """Valide le fichier donné en argument et retourne le code de sortie."""

    analyseur = argparse.ArgumentParser(description="Valide un niveau du jeu Paxman.")
    analyseur.add_argument("fichier", help="chemin du fichier de niveau (.json)")
    analyseur.add_argument(
        "--carte",
        action="store_true",
        help="affiche le plateau en marquant d'un X les pilules inatteignables",
    )
    arguments = analyseur.parse_args(argv)

    try:
        with open(arguments.fichier, encoding="utf-8") as fichier:
            config = json.load(fichier)
    except (OSError, json.JSONDecodeError) as erreur:
        print(f"✗ impossible de lire {arguments.fichier} : {erreur}")
        return 2

    rapport = Rapport()
    niveau = valider(config, rapport)

    for message in rapport.erreurs:
        print(f"✗ ERREUR        {message}")
    for message in rapport.avertissements:
        print(f"! AVERTISSEMENT {message}")

    if niveau is not None and arguments.carte:
        print()
        print(dessiner_carte(niveau, config))
        print()

    if rapport.valide:
        recompenses = len(niveau.recompenses()) if niveau else 0
        print(
            f"✓ {arguments.fichier} est valide "
            f"({niveau.largeur}×{niveau.hauteur} tuiles, {recompenses} récompenses)"
        )
        return 0

    print(f"\n✗ {arguments.fichier} est invalide ({len(rapport.erreurs)} erreur(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())

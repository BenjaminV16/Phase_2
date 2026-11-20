"""Module sonore du jeu Paxman — fourni, rien à y modifier.

Les fichiers sonores sont attendus dans le dossier `sons/`, à la racine du
projet, au format `.wav` :

    sons/sirène.wav
    sons/mange-pilule.wav
    sons/mange-fantôme.wav
    sons/fantômes-enfuite.wav
    sons/paxman-requiem.wav

Si un fichier est absent ou illisible, le lecteur correspondant devient
silencieux : le jeu continue de fonctionner normalement, et un avertissement
est affiché une seule fois au démarrage. L'option `--sourdine` rend tous les
lecteurs silencieux d'un coup.
"""

from __future__ import annotations

import pathlib
import sys

import pyglet
from pyglet.media.exceptions import MediaException
from pyglet.util import DecodeException

# le nom de chaque son, et s'il doit tourner en boucle
SONS = {
    "sirène": True,
    "mange-pilule": False,
    "mange-fantôme": False,
    "fantômes-enfuite": True,
    "paxman-requiem": False,
}

# dossier par défaut des fichiers sonores, à la racine du projet
DOSSIER_PAR_DEFAUT = pathlib.Path(__file__).resolve().parent.parent / "sons"


class LecteurSon:
    """Un son du jeu, que l'on peut jouer et arrêter.

    Un lecteur sans source audio (fichier manquant, ou mode sourdine) se
    comporte exactement comme les autres, mais ne produit aucun son.
    """

    def __init__(self, nom: str, source=None, boucle: bool = False) -> None:
        self._nom = nom
        self._source = source
        self._boucle = boucle
        self._lecteur: pyglet.media.Player | None = None

    @property
    def nom(self) -> str:
        """Retourne le nom de ce son."""

        return self._nom

    @property
    def silencieux(self) -> bool:
        """Indique si ce lecteur est muet (fichier absent ou mode sourdine)."""

        return self._source is None

    def jouer(self) -> None:
        """Démarre ce son depuis le début.

        Si le son tourne déjà, il est relancé : c'est ce que l'on veut pour un
        effet court comme `mange-pilule`, joué plusieurs fois par seconde.
        """

        if self._source is None:
            return

        self.arreter()
        self._lecteur = pyglet.media.Player()
        self._lecteur.queue(self._source)
        self._lecteur.loop = self._boucle
        self._lecteur.play()

    def arreter(self) -> None:
        """Arrête ce son s'il est en train de jouer."""

        if self._lecteur is not None:
            self._lecteur.pause()
            self._lecteur.delete()
            self._lecteur = None

    def en_lecture(self) -> bool:
        """Indique si ce son est en train de jouer."""

        return self._lecteur is not None

    def __repr__(self) -> str:
        etat = "silencieux" if self.silencieux else "prêt"
        return f"<LecteurSon {self._nom!r} ({etat})>"


def charger_les_sons(dossier: pathlib.Path | None = None,
                     sourdine: bool = False) -> dict[str, LecteurSon]:
    """Construit le dictionnaire des lecteurs de son du jeu.

    La clé est le nom du son (`"mange-pilule"`, ...), la valeur un `LecteurSon`.
    Le dictionnaire contient toujours tous les sons, même en mode sourdine ou
    si les fichiers sont absents : votre code peut donc les appeler sans jamais
    vérifier quoi que ce soit.
    """

    dossier = pathlib.Path(dossier) if dossier else DOSSIER_PAR_DEFAUT
    lecteurs: dict[str, LecteurSon] = {}
    manquants: list[str] = []

    for nom, boucle in SONS.items():
        source = None

        if not sourdine:
            fichier = dossier / f"{nom}.wav"
            if fichier.exists():
                try:
                    source = pyglet.media.load(str(fichier), streaming=boucle)
                except (OSError, MediaException, DecodeException):
                    manquants.append(f"{nom} (illisible)")
            else:
                manquants.append(nom)

        lecteurs[nom] = LecteurSon(nom, source, boucle)

    if manquants:
        print(
            "Attention : son(s) indisponible(s) — " + ", ".join(manquants) + ".\n"
            f"            Déposez les fichiers .wav dans {dossier}.\n"
            "            Le jeu fonctionne normalement, mais en silence.",
            file=sys.stderr,
        )

    return lecteurs


def arreter_tous(lecteurs: dict[str, LecteurSon]) -> None:
    """Arrête tous les sons en cours de lecture."""

    for lecteur in lecteurs.values():
        lecteur.arreter()

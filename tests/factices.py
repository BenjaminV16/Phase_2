"""Doublures des modules graphiques et sonores — FOURNI, rien à modifier.

La phase 2 se joue dans `JeuPaxman`, qui ouvre normalement une fenêtre pyglet
et charge des sons. On ne veut ni l'un ni l'autre pendant les tests : une
fenêtre qui s'ouvre et se ferme à chaque test est lente, et elle empêcherait
les tests de s'exécuter sur une machine sans écran.

On remplace donc, *avant* le premier `import paxman.jeu`, les deux modules
concernés par des imitations qui ont les mêmes méthodes mais ne dessinent et
ne jouent rien. En prime, elles notent ce qu'on leur demande : c'est ainsi que
les tests peuvent vérifier qu'un minuteur a bien été programmé ou qu'un son a
bien été joué.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Callable

# --------------------------------------------------------------- la fenêtre --


class FenetreFactice:
    """Imite `paxman.fenetre_pyglet.Fenetre` sans rien afficher."""

    def __init__(self, _plateau, reglages, **_kwargs) -> None:
        # les réglages du jeu : c'est le même dictionnaire que celui du jeu,
        # si bien qu'un test peut y changer une durée avant d'agir
        self.reglages = reglages

        # l'entête, qui démarre comme dans la vraie fenêtre
        self.score = types.SimpleNamespace(text="Score: 0")

        # état de la manette, que les tests peuvent imposer
        self.manette = (0, 0)
        self.accelerateur = False

        # minuteurs programmés, dans l'ordre : (fonction, délai, intervalle) ;
        # comme avec pyglet, programmer deux fois la même fonction donne deux
        # minuteurs, tant qu'on n'annule pas le premier
        self.minuteurs: list[tuple[Callable, float, bool]] = []

        # nombre d'appels à chaque méthode de dessin
        self.dessins: dict[str, int] = {}

    @staticmethod
    def temps_ecoule() -> float:
        """Imite le chronomètre de la fenêtre : le temps est figé."""

        return 0.0

    # --- les minuteurs ------------------------------------------------------

    def programmer_appel_fonction(self, fonction, delai, intervalle=False):
        """Note qu'un appel à `fonction` est programmé dans `delai` secondes."""

        self.minuteurs.append((fonction, delai, intervalle))

    def annuler_appel_fonction(self, fonction):
        """Oublie l'appel programmé à `fonction`, s'il y en avait un."""

        self.minuteurs = [m for m in self.minuteurs if m[0] != fonction]

    # --- ce que les tests interrogent ---------------------------------------

    def delai_de(self, fonction) -> float | None:
        """Retourne le délai programmé pour cette fonction, ou None."""

        delais = [delai for f, delai, _ in self.minuteurs if f == fonction]
        return delais[-1] if delais else None

    def nombre_de_minuteurs(self, fonction) -> int:
        """Retourne le nombre de minuteurs en attente pour cette fonction."""

        return sum(1 for f, _, _ in self.minuteurs if f == fonction)

    def est_programmee(self, fonction) -> bool:
        """Indique si un minuteur est en attente pour cette fonction."""

        return self.nombre_de_minuteurs(fonction) > 0

    # --- le dessin, qui ne dessine rien -------------------------------------

    def _noter(self, nom: str) -> None:
        self.dessins[nom] = self.dessins.get(nom, 0) + 1

    def dessiner_obstacles(self, _plateau=None):
        """Imite le dessin des murs : on compte seulement les appels."""

        self._noter("obstacles")

    def dessiner_recompenses(self, _plateau=None):
        """Imite le dessin des récompenses : on compte seulement les appels."""

        self._noter("recompenses")

    def dessiner_paxman(self, _paxman=None):
        """Imite le dessin de Paxman : on compte seulement les appels."""

        self._noter("paxman")

    def dessiner_fantome(self, _fantome=None):
        """Imite le dessin d'un fantôme : on compte seulement les appels."""

        self._noter("fantome")

    def dessiner_cage(self, _emplacement=None):
        """Imite le dessin de la cage : on compte seulement les appels."""

        self._noter("cage")


# ----------------------------------------------------------------- les sons --


class LecteurFactice:
    """Imite `paxman.son_pyglet.LecteurSon` sans toucher à la carte de son."""

    def __init__(self, nom: str) -> None:
        self.nom = nom
        self.joue = 0          # nombre de fois où on a demandé la lecture
        self.arrete = 0        # nombre de fois où on l'a arrêté
        self._en_lecture = False

    def jouer(self) -> None:
        """Note une demande de lecture."""

        self.joue += 1
        self._en_lecture = True

    def arreter(self) -> None:
        """Note une demande d'arrêt."""

        self.arrete += 1
        self._en_lecture = False

    def en_lecture(self) -> bool:
        """Indique si le son est censé être en train de jouer."""

        return self._en_lecture


NOMS_DE_SONS = (
    "sirène",
    "mange-pilule",
    "mange-fantôme",
    "fantômes-enfuite",
    "paxman-requiem",
)

# les lecteurs du dernier jeu créé : c'est par là que les tests les consultent
SONS: dict[str, LecteurFactice] = {}

# la valeur de `sourdine` reçue lors du dernier chargement des sons
CHARGEMENT = {"sourdine": None}


def charger_les_sons(_dossier=None, sourdine=False) -> dict[str, LecteurFactice]:
    """Imite le chargement des sons : aucun fichier n'est lu."""

    CHARGEMENT["sourdine"] = sourdine
    SONS.clear()
    SONS.update({nom: LecteurFactice(nom) for nom in NOMS_DE_SONS})
    return SONS


def arreter_tous(lecteurs) -> None:
    """Arrête tous les lecteurs du dictionnaire."""

    for lecteur in lecteurs.values():
        lecteur.arreter()


# --------------------------------------------------- la mise en place -------


def installer() -> None:
    """Substitue les doublures aux vrais modules, avant tout import du jeu.

    Appelée par `conftest.py`, donc avant que pytest n'importe le moindre
    fichier de test. Si `paxman.jeu` était déjà importé, il serait trop tard :
    on le retire du cache pour forcer sa réimportation.
    """

    fenetre = types.ModuleType("paxman.fenetre_pyglet")
    fenetre.Fenetre = FenetreFactice
    sys.modules["paxman.fenetre_pyglet"] = fenetre

    son = types.ModuleType("paxman.son_pyglet")
    son.LecteurSon = LecteurFactice
    son.charger_les_sons = charger_les_sons
    son.arreter_tous = arreter_tous
    son.SONS = {nom: True for nom in NOMS_DE_SONS}
    sys.modules["paxman.son_pyglet"] = son

    sys.modules.pop("paxman.jeu", None)

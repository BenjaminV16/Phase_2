"""Ce module contient la définition de la classe qui encapsule le paxman."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .acteur import Acteur

if TYPE_CHECKING:
    from .jeu import JeuPaxman


class Paxman(Acteur):
    """Un paxman est l'acteur principal du jeu."""

    def __init__(self, x: int, y: int, *, reglages: dict[str, str | float]) -> None:
        # initialiser la position de Paxman
        super().__init__(x, y)

        # mémoriser ses réglages
        self._reglages = reglages

        # initialiser sa vitesse
        self.vitesse = self.reglage("vitesse-défaut")

        self.vies = self.reglage("vies")

        # initialiser son score
        self.score = 0

        # TODO (phase 2, étape 8) : initialiser ici la jauge d'accélération
        # de Paxman, un nombre réel entre 0 (vide) et 1 (pleine), à 1.
        self.jauge = 1.0

    @property
    def score(self) -> int:
        """Retourne le score actuel de Paxman."""

        return self._score

    @score.setter
    def score(self, valeur: int) -> None:
        """Définit le score de Paxman."""

        # valider la valeur
        if not isinstance(valeur, int):
            raise TypeError("le score doit être un entier")

        if valeur < 0:
            raise ValueError("Le score doit être supérieur ou égal à zéro")

        # mémoriser le nouveau score
        self._score = valeur

    def mettre_a_jour_la_jauge(self, accelere: bool, delta_t: float) -> bool:
        """Vide ou remplit la jauge d'accélération pendant une trame."""
        if not accelere:
            self.jauge = min(1.0, self.jauge + self.reglage("jauge-recharge") * delta_t)
            return False

        if self.jauge <= 0:
            self.jauge = 0.0
            return False

        self.jauge = max(0.0, self.jauge - self.reglage("jauge-vidange") * delta_t)
        return True

        raise NotImplementedError

    def choisir_une_direction(self, jeu: "JeuPaxman") -> tuple[int, int]:
        """Choisit la prochaine direction de Paxman, sans manette (mode automatique).

        À implanter en phase 3. Pour l'instant, Paxman suit simplement la
        manette, comme en mode manuel : le mode automatique tourne donc, mais
        ne décide encore rien par lui-même.
        """

        return jeu.manette

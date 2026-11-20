"""Tests automatiques de la phase 1 — exemple.

Ces tests s'exécutent **sans fenêtre graphique et sans pyglet** : les modules
`plateau`, `acteur`, `objet`, `obstacles` et `recompenses` n'en dépendent pas.
L'étudiant peut donc vérifier son travail avant de remettre :

    python3 -m pytest tests/ -v

Les tests marqués « à implanter » portent sur les petites fonctions que
l'étudiant doit ajouter à la coquille en phase 1.
"""

import pytest

from paxman.acteur import Acteur
from paxman.obstacles import Mur, Porte
from paxman.plateau import Plateau
from paxman.recompenses import Pilule, PiluleForce

PETIT_PLATEAU = [
    "┌────┐",
    "│....│",
    "│.┌┐o│",
    "│.└┘.│",
    "└────┘",
]


@pytest.fixture(name="plateau")
def fixture_plateau():
    """Un petit plateau de 6 × 5 tuiles, avec 8 récompenses."""

    return Plateau(description=PETIT_PLATEAU)


# ------------------------------------------------- ce qui est déjà fourni ---


class TestPlateauFourni:
    """Vérifie la compréhension du plateau (rien à coder, tout est fourni)."""

    def test_dimensions(self, plateau):
        """Le plateau mesure 6 tuiles de large et 5 de haut."""

        assert (plateau.largeur, plateau.hauteur) == (6, 5)

    def test_origine_en_bas_a_gauche(self, plateau):
        """La tuile (1, 1) est en bas à gauche, et non en haut."""

        assert isinstance(plateau[(1, 1)], Mur)
        assert isinstance(plateau[(2, 4)], Pilule)

    def test_pilule_de_force(self, plateau):
        """Le caractère « o » devient une pilule de force de 100 points."""

        assert isinstance(plateau[(5, 3)], PiluleForce)
        assert plateau[(5, 3)].points == 100

    def test_mur_infranchissable(self, plateau):
        """Un couloir est franchissable, un mur ne l'est pas."""

        assert plateau.tuile_franchissable((2, 2)) is True
        assert plateau.tuile_franchissable((1, 3)) is False

    def test_tunnel_boucle_sur_lui_meme(self, plateau):
        """Sortir d'un côté du plateau fait rentrer de l'autre."""

        assert plateau.normaliser_coordonnees((7, 3)) == (1, 3)
        assert plateau.normaliser_coordonnees((0, 3)) == (6, 3)


class TestDeplacementFourni:
    """Vérifie la compréhension de `Acteur.deplacer` (fourni)."""

    def test_avance_a_la_vitesse(self, plateau):
        """Un acteur parcourt vitesse × delta_t tuiles en une trame."""

        acteur = Acteur(2.0, 2.0)
        acteur.vitesse = 4.0
        acteur.deplacer((0, 1), 0.25, plateau)  # 4 tuiles/s pendant 1/4 s
        assert acteur.position == pytest.approx((2.0, 3.0))

    def test_rebondit_sur_un_mur(self, plateau):
        """Un acteur lancé contre un mur s'arrête devant lui."""

        acteur = Acteur(2.0, 4.0)
        acteur.vitesse = 10.0
        acteur.deplacer((0, 1), 1.0, plateau)  # un mur se trouve en (2, 5)
        assert acteur.position == pytest.approx((2.0, 4.0))

    def test_direction_invalide_refusee(self):
        """Une direction en diagonale est refusée."""

        with pytest.raises(ValueError):
            Acteur(1, 1).direction = (1, 1)


class TestAccelerationFournie:
    """Vérifie le facteur de vitesse, sur lequel repose la touche espace."""

    def test_facteur_neutre_au_depart(self):
        """Un acteur neuf a un facteur de vitesse de 1."""

        assert Acteur(1, 1).facteur == 1.0

    def test_facteur_invalide_refuse(self):
        """Un facteur nul ou négatif est refusé."""

        with pytest.raises(ValueError):
            Acteur(1, 1).facteur = 0

    def test_facteur_multiplie(self, plateau):
        """Doubler le facteur double la distance parcourue."""

        parcourues = []
        for facteur in (1.0, 2.0):
            acteur = Acteur(2.0, 2.0)
            acteur.vitesse = 2.0
            acteur.facteur = facteur
            acteur.deplacer((0, 1), 0.25, plateau)
            parcourues.append(acteur.position[1] - 2.0)

        assert parcourues[0] == pytest.approx(0.5)
        assert parcourues[1] == pytest.approx(1.0)

    def test_vitesse_de_base_intacte(self):
        """Le facteur n'écrase pas `vitesse` : les deux se composent."""

        acteur = Acteur(1, 1)
        acteur.vitesse = 4.5
        acteur.facteur = 1.4
        assert acteur.vitesse == 4.5


# ------------------------------------------------------- à implanter --------


class TestAImplanterPhase1:
    """Petites fonctions que l'équipe doit ajouter en phase 1."""

    def test_compter_les_recompenses(self, plateau):
        """Le petit plateau contient 8 récompenses."""

        # Plateau.compter_recompenses() -> int
        assert plateau.compter_recompenses() == 8

    def test_recompense_sur_une_tuile(self, plateau):
        """recompense_a retourne la récompense d'une tuile, ou None."""

        # Plateau.recompense_a(tuile) -> Recompense | None
        assert isinstance(plateau.recompense_a((2, 4)), Pilule)
        assert plateau.recompense_a((1, 1)) is None

    def test_voisines_franchissables(self, plateau):
        """voisines retourne seulement les tuiles adjacentes franchissables."""

        # Plateau.voisines(tuile) -> liste des tuiles franchissables adjacentes
        assert sorted(plateau.voisines((2, 3))) == [(2, 2), (2, 4)]

    def test_ramasser_retire(self, plateau):
        """ramasser retire la récompense et retourne ses points."""

        # Plateau.ramasser(tuile) -> int (les points gagnés)
        points = plateau.ramasser((5, 3))
        assert points == 100
        assert plateau.recompense_a((5, 3)) is None
        assert plateau.compter_recompenses() == 7

    def test_ramasser_tuile_vide(self, plateau):
        """Ramasser sur une tuile sans récompense rapporte 0 point."""

        assert plateau.ramasser((1, 1)) == 0

    def test_gagnee_si_plateau_vide(self, plateau):
        """La partie est gagnée quand il ne reste plus aucune récompense."""

        for tuile in [t for t, o in list(plateau.items()) if isinstance(o, Pilule)]:
            plateau.ramasser(tuile)
        assert plateau.compter_recompenses() == 0
        assert plateau.partie_gagnee() is True


class TestPorte:
    """Vérifie l'ouverture des portes de la cage (fourni)."""

    def test_porte_fermee_puis_ouverte(self):
        """Une porte est fermée au départ, puis peut être ouverte."""

        porte = Porte(1, 1, sorte="_")
        assert porte.ouverture is False
        porte.ouverture = True
        assert porte.ouverture is True

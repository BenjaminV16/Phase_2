"""Contrôle — Mouvement de Paxman et des fantômes (acquis de la phase 1, non noté).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pytest

from .aides import (
    paxman_lance,
    plateau_en_couloirs,
)

TRAME = 1 / 60


class TestControleMouvement:
    """Contrôle — Mouvement de Paxman et des fantômes.
    
    Travail de la phase 1, déjà dans la coquille : ces tests passent dès le
    départ et doivent continuer de passer. Ils ne comptent dans aucun critère."""

    @pytest.mark.point("les flèches du clavier pilotent Paxman")
    @pytest.mark.parametrize("fleche", [(1, 0), (-1, 0)])
    def test_la_manette_pilote_paxman(self, jeu, fleche):
        """Dans la partie, la flèche enfoncée fait avancer Paxman dans sa direction."""

        depart = jeu.paxman.position[0]
        jeu.fenetre.manette = fleche

        for _ in range(20):
            jeu.animer_le_jeu(TRAME)

        assert (jeu.paxman.position[0] - depart) * fleche[0] > 0.5

    @pytest.mark.point("flèche tenue : Paxman vire dès que c'est possible")
    @pytest.mark.parametrize(
        "vertical, fleche, arrivee",
        [
            (False, (0, 1), (4, 4)),      # couloir horizontal, flèche vers le haut
            (False, (0, -1), (4, 2)),     # couloir horizontal, flèche vers le bas
            (True, (1, 0), (4, 4)),       # couloir vertical, flèche vers la droite
            (True, (-1, 0), (2, 4)),      # couloir vertical, flèche vers la gauche
        ],
    )
    def test_vire_des_que_possible(self, vertical, fleche, arrivee):
        """Flèche tenue : Paxman vire à la première ouverture, puis s'arrête contre le mur."""

        plateau = plateau_en_couloirs(vertical)
        paxman = paxman_lance(vertical)

        for _ in range(120):
            paxman.deplacer(fleche, TRAME, plateau)

        assert paxman.position == pytest.approx(arrivee)

    @pytest.mark.point("en attendant, Paxman continue tout droit")
    @pytest.mark.parametrize("fleche", [(0, 1), (0, -1)])
    def test_continue_tout_droit(self, fleche):
        """En attendant une ouverture, Paxman garde sa direction sans s'arrêter."""

        plateau = plateau_en_couloirs()
        paxman = paxman_lance()
        abscisses = []

        # 10 trames à 4,5 tuiles/s : 0,75 tuile, avant la première ouverture
        for _ in range(10):
            paxman.deplacer(fleche, TRAME, plateau)
            abscisses.append(paxman.position[0])
            assert paxman.position[1] == pytest.approx(3.0)

        assert abscisses == sorted(abscisses) and abscisses[-1] > 3.5

    @pytest.mark.point("en attendant, Paxman continue tout droit")
    def test_sans_fleche_il_continue(self):
        """Sans flèche enfoncée, Paxman poursuit sa route dans la même direction."""

        plateau = plateau_en_couloirs()
        paxman = paxman_lance()

        for _ in range(10):
            paxman.deplacer((0, 0), TRAME, plateau)

        assert paxman.position[0] > 3.5 and paxman.direction == (1, 0)

    @pytest.mark.point("les fantômes suivent leur algorithme")
    def test_chaque_fantome_bouge(self, jeu):
        """Une fois les portes ouvertes, les quatre fantômes se déplacent."""

        jeu.ouvrir_les_portes(0)
        departs = {nom: fantome.position for nom, fantome in jeu.fantomes.items()}

        for _ in range(60):
            jeu.animer_le_jeu(TRAME)

        immobiles = [nom for nom, depart in departs.items() if jeu.fantomes[nom].position == depart]

        assert not immobiles, f"fantômes restés immobiles : {immobiles}"

    @pytest.mark.point("les fantômes suivent leur algorithme")
    def test_blinky_disperse(self, jeu):
        """En dispersion, Blinky vise sa cible de dispersion."""

        blinky = jeu.fantomes["Blinky"]
        jeu.animer_le_jeu(TRAME)

        assert blinky.cible == pytest.approx(blinky.reglage("cible-dispersion"))

    @pytest.mark.point("les fantômes suivent leur algorithme")
    def test_blinky_poursuit(self, jeu):
        """En poursuite, Blinky vise la position de Paxman."""

        jeu.alterner_dispersion_poursuite(0)      # dispersion -> poursuite
        blinky = jeu.fantomes["Blinky"]
        jeu.animer_le_jeu(TRAME)

        assert blinky.cible == pytest.approx(jeu.paxman.position)

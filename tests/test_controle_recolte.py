"""Contrôle — Récolte des récompenses (acquis de la phase 1, non noté).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pytest

from paxman.recompenses import PiluleForce
from .aides import (
    placer_paxman_sur,
    tuile_d_une_pilule_simple,
    tuiles_des_pilules,
)

TRAME = 1 / 60


class TestControleRecolte:
    """Contrôle — Récolte des récompenses.
    
    Travail de la phase 1, déjà dans la coquille : ces tests passent dès le
    départ et doivent continuer de passer. Ils ne comptent dans aucun critère."""

    @pytest.mark.point("la récompense est retirée du plateau")
    @pytest.mark.parametrize("nombre", [1, 5])
    def test_pilules_retirees(self, jeu, nombre):
        """Une récompense ramassée disparaît du plateau."""

        avant = jeu.plateau.compter_recompenses()
        tuiles = tuiles_des_pilules(jeu)[:nombre]
        for tuile in tuiles:
            placer_paxman_sur(jeu, tuile)
            jeu.ramasser_la_recompense()

        assert jeu.plateau.compter_recompenses() == avant - nombre
        restees = [tuile for tuile in tuiles if jeu.plateau.recompense_a(tuile) is not None]
        assert not restees, f"récompenses encore sur le plateau : {restees}"

    @pytest.mark.point("la récompense est retirée du plateau")
    def test_case_vide_ne_rapporte_rien(self, jeu):
        """Repasser sur une tuile déjà vidée ne rapporte plus rien."""

        tuile = tuile_d_une_pilule_simple(jeu)
        placer_paxman_sur(jeu, tuile)
        jeu.ramasser_la_recompense()
        jeu.ramasser_la_recompense()

        assert jeu.paxman.score == 10

    @pytest.mark.point("le score augmente des points de la récompense")
    @pytest.mark.parametrize("nombre", [1, 3, 10])
    def test_points_des_pilules(self, jeu, nombre):
        """Chaque pilule ordinaire ramassée ajoute 10 points au score."""

        simples = [t for t in tuiles_des_pilules(jeu)
                   if t not in tuiles_des_pilules(jeu, PiluleForce)]
        for tuile in simples[:nombre]:
            placer_paxman_sur(jeu, tuile)
            jeu.ramasser_la_recompense()

        assert jeu.paxman.score == 10 * nombre

    @pytest.mark.point("le score augmente des points de la récompense")
    def test_points_pilule_de_force(self, jeu):
        """Une pilule de force ajoute 100 points au score."""

        placer_paxman_sur(jeu, tuiles_des_pilules(jeu, PiluleForce)[0])
        jeu.ramasser_la_recompense()

        assert jeu.paxman.score == 100

    @pytest.mark.point("le score augmente des points de la récompense")
    def test_ramassee_en_jouant(self, jeu):
        """En jouant, passer sur une pilule la ramasse, sans appel explicite."""

        placer_paxman_sur(jeu, tuile_d_une_pilule_simple(jeu))
        jeu.animer_le_jeu(TRAME)

        assert jeu.paxman.score == 10

    @pytest.mark.point("le score est affiché dans la fenêtre")
    @pytest.mark.parametrize("score", [0, 250, 9999])
    def test_score_dans_l_entete(self, jeu, score):
        """Le score courant est affiché dans l'entête de la fenêtre."""

        jeu.paxman.score = score
        jeu.animer_le_jeu(TRAME)

        assert str(score) in jeu.fenetre.score.text

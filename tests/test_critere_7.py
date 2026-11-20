"""Critère 7 — Jauge d'accélération (étape 8).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pytest

from .aides import (
    creer_paxman,
)

TRAME = 1 / 60


class TestCritere7Jauge:
    """Critère 7 — Jauge d'accélération (étape 8)."""

    @pytest.mark.point("la jauge démarre pleine et reste entre 0 et 1")
    def test_jauge_pleine_au_depart(self, jeu):
        """La jauge de Paxman est pleine (1.0) au début de la partie."""

        assert jeu.paxman.jauge == pytest.approx(1.0)

    @pytest.mark.point("la jauge démarre pleine et reste entre 0 et 1")
    @pytest.mark.parametrize("depart", [0.0, 0.3, 0.99, 1.0])
    def test_bornes(self, depart):
        """La jauge reste toujours entre 0 et 1, dans un sens comme dans l'autre."""

        plein = creer_paxman()
        plein.jauge = depart
        plein.mettre_a_jour_la_jauge(False, 100.0)

        vide = creer_paxman()
        vide.jauge = depart
        vide.mettre_a_jour_la_jauge(True, 100.0)

        assert plein.jauge == pytest.approx(1.0)
        assert vide.jauge == pytest.approx(0.0)

    @pytest.mark.point("elle se vide selon « jauge-vidange »")
    @pytest.mark.parametrize("vidange, duree", [(0.25, 1.0), (0.5, 0.5), (1.0, 0.3), (2.0, 0.1)])
    def test_vidange(self, vidange, duree):
        """Accélérer pendant `duree` secondes retire vidange × duree à une jauge pleine."""

        paxman = creer_paxman(jauge_vidange=vidange)

        assert paxman.mettre_a_jour_la_jauge(True, duree) is True
        assert paxman.jauge == pytest.approx(1.0 - vidange * duree)

    @pytest.mark.point("elle se vide selon « jauge-vidange »")
    @pytest.mark.parametrize("vidange", [0.25, 0.5, 1.0])
    def test_duree_d_une_jauge_pleine(self, vidange):
        """Une jauge pleine permet d'accélérer pendant 1 / vidange secondes, pas plus."""

        paxman = creer_paxman(jauge_vidange=vidange)
        trames = 0

        while paxman.mettre_a_jour_la_jauge(True, TRAME) and trames < 10_000:
            trames += 1

        assert trames * TRAME == pytest.approx(1 / vidange, abs=2 * TRAME)

    @pytest.mark.point("elle se vide selon « jauge-vidange »")
    def test_pas_de_triche_au_rythme(self):
        """60 trames de 1/60 s vident autant la jauge qu'une seule trame de 1 s."""

        lent = creer_paxman()
        for _ in range(60):
            lent.mettre_a_jour_la_jauge(True, TRAME)

        rapide = creer_paxman()
        rapide.mettre_a_jour_la_jauge(True, 1.0)

        assert lent.jauge == pytest.approx(rapide.jauge)

    @pytest.mark.point("elle se remplit selon « jauge-recharge »")
    @pytest.mark.parametrize("recharge, duree", [(0.1, 1.0), (0.2, 2.0), (0.5, 0.4), (1.0, 0.25)])
    def test_recharge(self, recharge, duree):
        """Relâcher pendant `duree` secondes ajoute recharge × duree à une jauge vide."""

        paxman = creer_paxman(jauge_recharge=recharge)
        paxman.jauge = 0.0

        assert paxman.mettre_a_jour_la_jauge(False, duree) is False
        assert paxman.jauge == pytest.approx(recharge * duree)

    @pytest.mark.point("elle se remplit selon « jauge-recharge »")
    @pytest.mark.parametrize("recharge", [0.1, 0.2, 0.5])
    def test_duree_d_une_recharge(self, recharge):
        """Une jauge vide se remplit complètement en 1 / recharge secondes."""

        paxman = creer_paxman(jauge_recharge=recharge)
        paxman.jauge = 0.0

        for _ in range(round(60 / recharge)):
            paxman.mettre_a_jour_la_jauge(False, TRAME)

        assert paxman.jauge == pytest.approx(1.0)

    @pytest.mark.point("elle se remplit selon « jauge-recharge »")
    def test_relacher_recharge_en_jeu(self, jeu):
        """Dans la partie, relâcher l'espace recharge la jauge à chaque trame."""

        jeu.paxman.jauge = 0.0
        jeu.fenetre.accelerateur = False
        for _ in range(60):
            jeu.ajuster_acceleration(TRAME)

        assert jeu.paxman.jauge == pytest.approx(jeu.paxman.reglage("jauge-recharge"))

    @pytest.mark.point("jauge vide : plus d'accélération ni de recharge")
    @pytest.mark.parametrize("trames", [1, 60, 600])
    def test_vide_et_touche_tenue(self, trames):
        """Tant qu'on garde la touche enfoncée, une jauge vide reste vide."""

        paxman = creer_paxman()
        paxman.jauge = 0.0

        permis = [paxman.mettre_a_jour_la_jauge(True, TRAME) for _ in range(trames)]

        assert not any(permis), "Paxman a pu accélérer avec une jauge vide"
        assert paxman.jauge == pytest.approx(0.0)

    @pytest.mark.point("jauge vide : plus d'accélération ni de recharge")
    def test_espace_tenu_trois_s(self, jeu):
        """Dans la partie, garder l'espace 3 s épuise la jauge et Paxman revient à 1."""

        jeu.fenetre.accelerateur = True
        for _ in range(180):
            jeu.ajuster_acceleration(TRAME)

        assert jeu.paxman.jauge == pytest.approx(0.0)
        assert jeu.paxman.facteur == pytest.approx(1.0)

    @pytest.mark.point("la jauge est affichée dans la fenêtre")
    @pytest.mark.parametrize("jauge", [0.0, 0.5])
    def test_entete_suit_la_jauge(self, jeu, jauge):
        """L'entête n'est pas la même avec une jauge pleine et une jauge entamée."""

        jeu.animer_le_jeu(TRAME)
        pleine = jeu.fenetre.score.text

        jeu.paxman.jauge = jauge
        jeu.animer_le_jeu(TRAME)

        assert jeu.fenetre.score.text != pleine, (
            f"l'entête ne change pas avec la jauge : {pleine!r}"
        )

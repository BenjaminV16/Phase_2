"""Critère 4 — Collisions, vies et fin de partie (étapes 2, 3 et 4).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import re

import pytest

from .aides import (
    rendre_dangereux,
    vider_le_plateau,
)

TRAME = 1 / 60


class TestCritere4Collisions:
    """Critère 4 — Collisions, vies et fin de partie (étapes 2, 3 et 4)."""

    @pytest.mark.point("fantôme en fuite : il devient « revenant »")
    def test_revenant_inoffensif(self, jeu, fantome):
        """Un fantôme dévoré (« revenant ») ne coûte pas de vie s'il touche encore Paxman."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)
        vies = jeu.paxman.vies

        arret = jeu.traiter_la_collision(fantome)

        assert jeu.paxman.vies == vies, "Paxman a perdu une vie contre un fantôme revenant"
        assert arret is False, "la trame s'arrête alors que le fantôme est inoffensif"

    @pytest.mark.point("fantôme en fuite : il devient « revenant »")
    @pytest.mark.parametrize("nom", ["Blinky", "Pinky", "Inky", "Clyde"])
    def test_devore_devient_revenant(self, jeu, nom):
        """Chaque fantôme dévoré passe en mode « revenant »."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(jeu.fantomes[nom])

        assert jeu.fantomes[nom].mode == "revenant"

    @pytest.mark.point("fantôme en fuite : il devient « revenant »")
    def test_trame_continue_si_devore(self, jeu):
        """Dévorer un fantôme retourne False : la trame se poursuit avec les suivants."""

        jeu.appliquer_la_pilule_force()
        resultats = [jeu.traiter_la_collision(f) for f in jeu.fantomes.values()]

        assert resultats == [False] * 4

    @pytest.mark.point("combo : 200, 400, 800 puis 1600 points")
    @pytest.mark.parametrize(
        "rang, attendu",
        [(1, 200), (2, 400), (3, 800), (4, 1600)],
    )
    def test_valeur_du_n_ieme_fantome(self, jeu, rang, attendu):
        """Le n-ième fantôme dévoré après une pilule vaut 200 × 2^(n-1) points."""

        jeu.appliquer_la_pilule_force()
        fantomes = list(jeu.fantomes.values())

        for fantome in fantomes[: rang - 1]:
            jeu.traiter_la_collision(fantome)

        avant = jeu.paxman.score
        jeu.traiter_la_collision(fantomes[rang - 1])

        assert jeu.paxman.score - avant == attendu

    @pytest.mark.point("combo : 200, 400, 800 puis 1600 points")
    def test_quatre_fantomes_3000(self, jeu):
        """Dévorer les quatre fantômes d'une même pilule rapporte 3000 points."""

        jeu.appliquer_la_pilule_force()
        avant = jeu.paxman.score

        for fantome in jeu.fantomes.values():
            jeu.traiter_la_collision(fantome)

        assert jeu.paxman.score - avant == 3000

    @pytest.mark.point("combo : 200, 400, 800 puis 1600 points")
    def test_combo_coupe_par_collision(self, jeu):
        """Après une collision fatale, la pilule suivante fait repartir le combo à 200."""

        jeu.appliquer_la_pilule_force()
        fantomes = list(jeu.fantomes.values())
        jeu.traiter_la_collision(fantomes[0])      # 200, combo -> 400

        fantomes[1].mode = "poursuite"             # celui-ci est dangereux
        jeu.traiter_la_collision(fantomes[1])      # coûte une vie

        jeu.appliquer_la_pilule_force()
        avant = jeu.paxman.score
        jeu.traiter_la_collision(fantomes[2])

        assert jeu.paxman.score - avant == 200

    @pytest.mark.point("autre fantôme : Paxman perd une vie")
    @pytest.mark.parametrize("mode", ["dispersion", "poursuite"])
    def test_seule_la_fuite_devorable(self, jeu, fantome, mode):
        """Un fantôme qui n'est pas en « fuite » ne se mange pas : la collision est fatale."""

        fantome.mode = mode
        vies = jeu.paxman.vies

        jeu.traiter_la_collision(fantome)

        assert jeu.paxman.vies == vies - 1

    @pytest.mark.point("autre fantôme : Paxman perd une vie")
    @pytest.mark.parametrize("vies", [2, 3, 5])
    def test_decompte(self, jeu, vies):
        """Chaque collision fatale retire exactement une vie."""

        jeu.paxman.vies = vies
        jeu.perdre_une_vie()

        assert jeu.paxman.vies == vies - 1

    @pytest.mark.point("autre fantôme : Paxman perd une vie")
    def test_trame_arretee_si_fatale(self, jeu, fantome):
        """Une collision fatale retourne True : la trame s'arrête là."""

        rendre_dangereux(jeu)

        assert jeu.traiter_la_collision(fantome) is True

    @pytest.mark.point("autre fantôme : Paxman perd une vie")
    def test_le_score_est_conserve(self, jeu):
        """Perdre une vie ne remet pas le score à zéro."""

        jeu.paxman.score = 1234
        jeu.perdre_une_vie()

        assert jeu.paxman.score == 1234

    @pytest.mark.point("acteurs replacés, READY!, pause de 2 s")
    def test_fantomes_en_cage(self, jeu):
        """Après la perte d'une vie, chaque fantôme reprend sa position initiale."""

        for fantome in jeu.fantomes.values():
            fantome.position = (1.0, 1.0)

        jeu.perdre_une_vie()

        hors_cage = [
            f.nom for f in jeu.fantomes.values()
            if f.position != tuple(f.reglage("position-initiale"))
        ]
        assert not hors_cage, f"fantômes non replacés : {hors_cage}"

    @pytest.mark.point("acteurs replacés, READY!, pause de 2 s")
    def test_acceleration_annulee(self, jeu):
        """Après la perte d'une vie, Paxman repart sans accélération (facteur 1)."""

        jeu.paxman.facteur = 1.4
        jeu.perdre_une_vie()

        assert jeu.paxman.facteur == pytest.approx(1.0)

    @pytest.mark.point("acteurs replacés, READY!, pause de 2 s")
    def test_pause_de_deux_secondes(self, jeu):
        """Après la perte d'une vie, la reprise est programmée 2 secondes plus tard."""

        jeu.perdre_une_vie()

        assert jeu.fenetre.delai_de(jeu.reprendre) == pytest.approx(2)

    @pytest.mark.point("acteurs replacés, READY!, pause de 2 s")
    def test_la_pause_se_termine(self, jeu):
        """Après la reprise, la partie est de nouveau animée."""

        jeu.perdre_une_vie()
        jeu.reprendre()
        position = jeu.paxman.position
        jeu.paxman.direction = (1, 0)
        jeu.fenetre.manette = (1, 0)
        jeu.animer_le_jeu(TRAME)

        assert jeu.en_pause is False and jeu.paxman.position != position

    @pytest.mark.point("acteurs replacés, READY!, pause de 2 s")
    def test_entete_annonce_ready(self, jeu):
        """Pendant la pause, l'entête de la fenêtre affiche READY!."""

        jeu.perdre_une_vie()

        assert "READY" in jeu.fenetre.score.text.upper()

    @pytest.mark.point("dernière vie perdue : la partie est perdue")
    @pytest.mark.parametrize("vies", [2, 3, 5, 10])
    def test_collisions_avant_la_fin(self, jeu, vies):
        """Une partie à n vies se termine exactement à la n-ième collision fatale."""

        jeu.paxman.vies = vies
        subies = 0

        with pytest.raises(StopIteration):
            for _ in range(vies + 5):
                jeu.perdre_une_vie()
                jeu.reprendre()
                subies += 1

        assert subies == vies - 1, (
            f"partie terminée à la collision n° {subies + 1} au lieu de la n° {vies}"
        )

    @pytest.mark.point("dernière vie perdue : la partie est perdue")
    def test_derniere_vie_stop(self, jeu):
        """Avec 2 vies, la première collision laisse jouer, la seconde termine la partie."""

        jeu.paxman.vies = 2
        jeu.perdre_une_vie()
        jeu.reprendre()

        with pytest.raises(StopIteration):
            jeu.perdre_une_vie()

    @pytest.mark.point("les vies restantes sont affichées")
    @pytest.mark.parametrize("score, vies", [(0, 3), (250, 2), (9999, 1)])
    def test_entete_affiche_les_deux(self, jeu, score, vies):
        """L'entête affiche à la fois le score et le nombre de vies restantes."""

        jeu.paxman.score = score
        jeu.paxman.vies = vies
        jeu.animer_le_jeu(TRAME)

        # \b : le nombre de vies doit apparaître seul, pas au milieu du score
        entete = jeu.fenetre.score.text
        assert re.search(rf"\b{score}\b", entete), f"entête : {entete!r}"
        assert re.search(rf"\b{vies}\b", entete), f"entête : {entete!r}"

    @pytest.mark.point("plus aucune récompense : la partie est gagnée")
    @pytest.mark.parametrize("restantes", [1, 2, 5])
    def test_la_partie_continue(self, jeu, restantes):
        """La partie continue tant qu'il reste une récompense, et s'arrête à la dernière."""

        vider_le_plateau(jeu, sauf=restantes)
        jeu.animer_le_jeu(TRAME)
        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

    @pytest.mark.point("plus aucune récompense : la partie est gagnée")
    def test_derniere_recompense(self, jeu):
        """La partie est gagnée dès que la dernière récompense disparaît."""

        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

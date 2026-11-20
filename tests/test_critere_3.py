"""Critère 3 — Pilules de force et fuite des fantômes (étape 1).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pytest

from .aides import (
    placer_paxman_sur,
    rendre_dangereux,
    tuile_d_une_pilule_simple,
)


class TestCritere3PiluleDeForce:
    """Critère 3 — Pilules de force et fuite des fantômes (étape 1)."""

    @pytest.mark.point("annule les minuteries d'une pilule encore active")
    @pytest.mark.parametrize("nombre", [2, 3, 5])
    def test_annule_le_premier_minuteur(self, jeu, nombre):
        """Après plusieurs pilules de suite, un seul minuteur de fin d'effet reste en attente."""

        for _ in range(nombre):
            jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.nombre_de_minuteurs(jeu.terminer_effet_pilule_force) == 1
        assert jeu.fenetre.nombre_de_minuteurs(jeu.signaler_fin_vulnerabilite) == 1

    @pytest.mark.point("annule les minuteries d'une pilule encore active")
    @pytest.mark.parametrize("nombre", [1, 2, 3, 5, 8])
    def test_pilules_successives(self, jeu, nombre):
        """Après plusieurs pilules de suite, la fin d'effet porte toujours la durée complète."""

        for _ in range(nombre):
            jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.delai_de(jeu.terminer_effet_pilule_force) == pytest.approx(
            jeu.reglage("fuite-durée")
        )

    @pytest.mark.point("programme la fin de l'effet selon « fuite-durée »")
    @pytest.mark.parametrize("duree", [1, 5, 12, 20, 30])
    def test_duree_de_l_effet(self, jeu, duree):
        """La fin de l'effet est programmée à « fuite-durée », quelle que soit sa valeur."""

        jeu.fenetre.reglages["fuite-durée"] = duree
        jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.delai_de(jeu.terminer_effet_pilule_force) == pytest.approx(duree)

    @pytest.mark.point("ajuste la vitesse selon « vitesse-force »")
    def test_vitesse_de_force(self, jeu):
        """Paxman prend exactement la vitesse du réglage « vitesse-force »."""

        jeu.appliquer_la_pilule_force()

        assert jeu.paxman.vitesse == jeu.paxman.reglage("vitesse-force")

    @pytest.mark.point("passe tous les fantômes en mode « fuite »")
    def test_tous_les_fantomes_fuient(self, jeu):
        """Les quatre fantômes passent en mode « fuite », sans exception."""

        rendre_dangereux(jeu)
        jeu.appliquer_la_pilule_force()

        modes = {f.nom: f.mode for f in jeu.fantomes.values()}

        assert set(modes.values()) == {"fuite"}, f"modes des fantômes : {modes}"

    @pytest.mark.point("passe tous les fantômes en mode « fuite »")
    def test_pilule_simple_sans_effet(self, jeu):
        """Seule une pilule de force fait fuir les fantômes, pas une pilule ordinaire."""

        rendre_dangereux(jeu)
        placer_paxman_sur(jeu, tuile_d_une_pilule_simple(jeu))
        jeu.ramasser_la_recompense()
        apres_la_simple = [f.mode for f in jeu.fantomes.values()]

        jeu.appliquer_la_pilule_force()

        assert "fuite" not in apres_la_simple
        modes = {f.nom: f.mode for f in jeu.fantomes.values()}
        assert set(modes.values()) == {"fuite"}, f"modes des fantômes : {modes}"

    @pytest.mark.point("remet le combo à 200 points")
    @pytest.mark.parametrize("pilules", [2, 3])
    def test_combo_repart_par_pilule(self, jeu, pilules):
        """Chaque pilule de force fait repartir le combo à 200, même après plusieurs séries."""

        gains = []
        for _ in range(pilules):
            jeu.appliquer_la_pilule_force()
            avant = jeu.paxman.score
            jeu.traiter_la_collision(next(iter(jeu.fantomes.values())))
            gains.append(jeu.paxman.score - avant)

        assert gains == [200] * pilules

    @pytest.mark.point("programme l'avertissement à 80 % de « fuite-durée »")
    @pytest.mark.parametrize("duree", [1, 5, 12, 20, 30])
    def test_avertissement_a_80(self, jeu, duree):
        """L'avertissement de fin de vulnérabilité est programmé à 80 % de la durée."""

        jeu.fenetre.reglages["fuite-durée"] = duree
        jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.delai_de(jeu.signaler_fin_vulnerabilite) == pytest.approx(
            0.8 * duree
        )

    @pytest.mark.point("à la fin, restaure vitesse, modes et alternance")
    def test_retour_vitesse_normale(self, jeu):
        """Paxman passe à « vitesse-force », puis retrouve « vitesse-défaut » à la fin."""

        jeu.appliquer_la_pilule_force()
        pendant = jeu.paxman.vitesse
        jeu.terminer_effet_pilule_force(0)

        assert pendant == jeu.paxman.reglage("vitesse-force")
        assert jeu.paxman.vitesse == jeu.paxman.reglage("vitesse-défaut")

    @pytest.mark.point("à la fin, restaure vitesse, modes et alternance")
    @pytest.mark.parametrize("mode", ["dispersion", "poursuite"])
    def test_modes_restaures(self, jeu, mode):
        """Les fantômes fuient pendant l'effet, puis reprennent le mode courant du jeu."""

        if mode == "poursuite":
            jeu.alterner_dispersion_poursuite(0)
        jeu.appliquer_la_pilule_force()
        pendant = [f.mode for f in jeu.fantomes.values()]
        jeu.terminer_effet_pilule_force(0)

        assert set(pendant) == {"fuite"}, f"modes pendant l'effet : {pendant}"
        apres = [f.mode for f in jeu.fantomes.values()]
        assert set(apres) == {mode}, f"modes après l'effet : {apres}"

    @pytest.mark.point("à la fin, restaure vitesse, modes et alternance")
    def test_revenant_reste_revenant(self, jeu, fantome):
        """Un fantôme déjà dévoré reste « revenant » à la fin de l'effet."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)
        jeu.terminer_effet_pilule_force(0)

        assert fantome.mode == "revenant"

    @pytest.mark.point("à la fin, restaure vitesse, modes et alternance")
    def test_alternance_suspendue(self, jeu):
        """Pendant l'effet, l'alternance dispersion/poursuite est annulée."""

        jeu.appliquer_la_pilule_force()

        assert not jeu.fenetre.est_programmee(jeu.alterner_dispersion_poursuite), (

            "l'alternance dispersion/poursuite est encore programmée"

        )

    @pytest.mark.point("à la fin, restaure vitesse, modes et alternance")
    def test_alternance_reprend(self, jeu):
        """L'alternance dispersion/poursuite est suspendue pendant l'effet, puis reprogrammée."""

        jeu.appliquer_la_pilule_force()
        suspendue = not jeu.fenetre.est_programmee(jeu.alterner_dispersion_poursuite)
        jeu.terminer_effet_pilule_force(0)

        assert suspendue, "l'alternance dispersion/poursuite n'a pas été annulée pendant l'effet"
        assert jeu.fenetre.est_programmee(jeu.alterner_dispersion_poursuite), (
            "l'alternance dispersion/poursuite n'a pas été reprogrammée"
        )

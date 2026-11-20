"""Critère 5 — Option --sourdine et intégration sonore (étapes 5 et 7).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pytest

from .aides import (
    analyser,
    executer_main,
    placer_paxman_sur,
    tuile_d_une_pilule_simple,
    tuiles_des_pilules,
    vider_le_plateau,
)

TRAME = 1 / 60


class TestCritere5Sons:
    """Critère 5 — Option --sourdine et intégration sonore (étapes 5 et 7)."""

    @pytest.mark.point("option --sourdine (mode sans son)")
    @pytest.mark.parametrize(
        "ligne, attendu",
        [
            ([], False),
            (["-s"], True),
            (["--sourdine"], True),
            (["-n", "1", "-s"], True),
            (["-d"], False),
        ],
    )
    def test_option_sourdine(self, monkeypatch, ligne, attendu):
        """L'option --sourdine (ou -s) est reconnue, seule ou combinée aux autres."""

        assert analyser(monkeypatch, ligne).sourdine is attendu

    @pytest.mark.point("option --sourdine (mode sans son)")
    @pytest.mark.parametrize(
        "ligne, attendu", [([], False), (["-s"], True), (["--sourdine"], True)]
    )
    def test_main_transmet_sourdine(self, monkeypatch, ligne, attendu):
        """main.py transmet toujours l'option à la partie : sourdine=True ou sourdine=False."""

        parties, _ = executer_main(monkeypatch, ligne)

        assert len(parties) == 1, f"main.py a créé {len(parties)} partie(s) au lieu d'une"
        assert parties[0].get("sourdine") is attendu, (
            f"JeuPaxman reçoit sourdine={parties[0].get('sourdine')} au lieu de {attendu}"
        )

    @pytest.mark.point("son quand Paxman mange une pilule")
    @pytest.mark.parametrize("pilules", [1, 2, 4])
    def test_un_son_par_pilule(self, jeu, sons, pilules):
        """Chaque récompense ramassée joue une fois le son « mange-pilule »."""

        for tuile in tuiles_des_pilules(jeu)[:pilules]:
            placer_paxman_sur(jeu, tuile)
            jeu.ramasser_la_recompense()

        assert sons["mange-pilule"].joue == pilules

    @pytest.mark.point("son quand Paxman mange une pilule")
    def test_pas_de_son_case_vide(self, jeu, sons):
        """Le son « mange-pilule » joue une fois pour la pilule, et plus sur la case vidée."""

        placer_paxman_sur(jeu, tuile_d_une_pilule_simple(jeu))
        jeu.ramasser_la_recompense()
        jeu.ramasser_la_recompense()

        assert sons["mange-pilule"].joue == 1

    @pytest.mark.point("musique de fuite après une pilule de force")
    def test_la_sirene_cede_la_place(self, jeu, sons):
        """Pendant l'effet d'une pilule, la sirène se tait au profit de « fantômes-enfuite »."""

        jeu.appliquer_la_pilule_force()

        assert not sons["sirène"].en_lecture(), "la sirène joue encore"
        assert sons["fantômes-enfuite"].en_lecture(), "la musique de fuite ne joue pas"

    @pytest.mark.point("son quand un fantôme est dévoré")
    @pytest.mark.parametrize("fantomes", [1, 2, 4])
    def test_un_son_par_fantome(self, jeu, sons, fantomes):
        """Chaque fantôme dévoré joue une fois le son « mange-fantôme »."""

        jeu.appliquer_la_pilule_force()
        for fantome in list(jeu.fantomes.values())[:fantomes]:
            jeu.traiter_la_collision(fantome)

        assert sons["mange-fantôme"].joue == fantomes

    @pytest.mark.point("requiem quand Paxman perd une vie")
    def test_requiem_seul(self, jeu, sons):
        """Perdre une vie arrête tous les sons avant de jouer « paxman-requiem »."""

        jeu.perdre_une_vie()
        autres = [
            nom for nom, lecteur in sons.items()
            if nom != "paxman-requiem" and lecteur.en_lecture()
        ]

        assert not autres, f"sons encore en lecture : {autres}"

    @pytest.mark.point("arrêt des sons en fin d'effet et en fin de partie")
    def test_la_sirene_revient(self, jeu, sons):
        """La musique de fuite joue pendant l'effet, puis la sirène reprend à la fin."""

        jeu.appliquer_la_pilule_force()
        pendant = sons["fantômes-enfuite"].en_lecture()
        jeu.terminer_effet_pilule_force(0)

        assert pendant, "la musique de fuite n'a pas démarré avec la pilule"
        assert sons["sirène"].en_lecture(), "la sirène n'a pas repris"
        assert not sons["fantômes-enfuite"].en_lecture(), "la musique de fuite joue encore"

    @pytest.mark.point("arrêt des sons en fin d'effet et en fin de partie")
    def test_victoire_coupe_les_sons(self, jeu, sons):
        """Une partie gagnée arrête tous les sons."""

        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

        en_lecture = [nom for nom, lecteur in sons.items() if lecteur.en_lecture()]

        assert not en_lecture, f"sons encore en lecture : {en_lecture}"

    @pytest.mark.point("arrêt des sons en fin d'effet et en fin de partie")
    def test_defaite_coupe_la_sirene(self, jeu, sons):
        """Une partie perdue arrête la sirène et ne laisse jouer que le requiem."""

        jeu.paxman.vies = 1

        with pytest.raises(StopIteration):
            jeu.perdre_une_vie()

        assert not sons["sirène"].en_lecture(), "la sirène joue encore"
        assert sons["paxman-requiem"].joue == 1

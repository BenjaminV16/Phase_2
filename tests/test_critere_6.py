"""Critère 6 — Option --lister-scores et fichier des scores (étapes 6 et 7).

Tests étendus de la phase 2 : les mêmes comportements que `test_phase2.py`,
sur beaucoup plus de valeurs.
Chaque test porte un marqueur `point` : le sous-critère de la grille qu'il
vérifie. Pour le bilan, lancez plutôt :

    python3 tests/noter_phase2.py
"""

import pathlib
import re

import pytest

import main
from .aides import (
    analyser,
    executer_main,
    vider_le_plateau,
)

TRAME = 1 / 60


def lire_les_scores() -> str:
    """Retourne le contenu du fichier des scores."""

    return pathlib.Path("scores.txt").read_text(encoding="utf-8")


class TestCritere6Scores:
    """Critère 6 — Option --lister-scores et fichier des scores (étapes 6 et 7)."""

    @pytest.mark.point("scores.txt est créé s'il est absent")
    def test_fichier_cree_si_absent(self, jeu):
        """scores.txt est créé automatiquement s'il n'existe pas encore."""

        assert not pathlib.Path("scores.txt").exists()
        jeu.sauvegarder_score()

        assert pathlib.Path("scores.txt").exists(), "scores.txt n'a pas été créé"

    @pytest.mark.point("scores.txt est créé s'il est absent")
    def test_defaite_enregistree(self, jeu):
        """Une partie perdue enregistre le score avant de lever StopIteration."""

        jeu.paxman.vies = 1
        jeu.paxman.score = 777

        with pytest.raises(StopIteration):
            jeu.perdre_une_vie()

        assert "777" in lire_les_scores()

    @pytest.mark.point("scores.txt est créé s'il est absent")
    def test_victoire_enregistree(self, jeu):
        """Une partie gagnée enregistre elle aussi le score."""

        jeu.paxman.score = 4242
        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

        assert "4242" in lire_les_scores()

    @pytest.mark.point("format « <date_iso> <score> »")
    def test_le_format_de_la_ligne(self, jeu):
        """Chaque ligne a la forme « 2026-03-20T16:42:10 1850 »."""

        jeu.paxman.score = 1850
        jeu.sauvegarder_score()

        ligne = lire_les_scores().strip()

        format_iso = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} 1850"
        assert re.fullmatch(format_iso, ligne), f"ligne écrite : {ligne!r}"

    @pytest.mark.point("format « <date_iso> <score> »")
    @pytest.mark.parametrize("score", [0, 7, 100, 1850, 123456])
    def test_le_score_ecrit(self, jeu, score):
        """Le score enregistré est bien celui de Paxman, quelle que soit sa valeur."""

        jeu.paxman.score = score
        jeu.sauvegarder_score()

        assert lire_les_scores().split()[1] == str(score)

    @pytest.mark.point("entrées dans l'ordre chronologique")
    def test_ordre_chronologique(self, jeu):
        """Les parties s'ajoutent au fichier dans l'ordre où elles ont été jouées."""

        for score in (300, 100, 200):
            jeu.paxman.score = score
            jeu.sauvegarder_score()

        assert lire_les_scores().split()[1::2] == ["300", "100", "200"]

    @pytest.mark.point("entrées dans l'ordre chronologique")
    @pytest.mark.parametrize("parties", [1, 2, 5])
    def test_une_ligne_par_partie(self, jeu, parties):
        """Le fichier des scores contient exactement une ligne par partie jouée."""

        for numero in range(parties):
            jeu.paxman.score = 100 * numero
            jeu.sauvegarder_score()

        assert len(lire_les_scores().strip().splitlines()) == parties

    @pytest.mark.point("entrées dans l'ordre chronologique")
    def test_fichier_pas_ecrase(self, jeu):
        """Une nouvelle partie s'ajoute à la fin du fichier existant."""

        pathlib.Path("scores.txt").write_text("2020-01-01T00:00:00 42\n", encoding="utf-8")
        jeu.paxman.score = 99
        jeu.sauvegarder_score()

        contenu = lire_les_scores()

        assert "42" in contenu, "l'ancienne partie a été effacée du fichier"
        assert "99" in contenu, "la nouvelle partie n'a pas été ajoutée au fichier"

    @pytest.mark.point("option --lister-scores")
    @pytest.mark.parametrize(
        "ligne, attendu",
        [
            ([], False),
            (["-l"], True),
            (["--lister-scores"], True),
            (["-l", "-s"], True),
        ],
    )
    def test_option_lister_scores(self, monkeypatch, ligne, attendu):
        """L'option --lister-scores (ou -l) est reconnue, seule ou combinée aux autres."""

        assert analyser(monkeypatch, ligne).lister_scores is attendu

    @pytest.mark.point("option --lister-scores")
    @pytest.mark.parametrize("option", ["-l", "--lister-scores"])
    def test_main_liste_sans_jouer(self, monkeypatch, tmp_path, capsys, option):
        """python3 main.py --lister-scores affiche les scores, puis quitte sans lancer de partie."""

        monkeypatch.chdir(tmp_path)
        pathlib.Path("scores.txt").write_text("2026-01-01T00:00:00 4321\n", encoding="utf-8")

        parties, code = executer_main(monkeypatch, [option])

        assert not parties, "main.py a lancé une partie au lieu de seulement lister les scores"

        assert code != 2, f"main.py ne reconnaît pas l'option {option}"
        assert code == 0, f"main.py s'est terminé avec le code {code}"
        assert "4321" in capsys.readouterr().out

    @pytest.mark.point("dix meilleurs, décroissants, un par ligne")
    def test_dix_meilleurs_seulement(self, tmp_path, capsys):
        """lister_les_scores affiche les dix meilleurs scores, un par ligne, du plus grand."""

        valeurs = [1003, 1011, 1001, 1015, 1007, 1002, 1014, 1009, 1005, 1012,
                   1006, 1013, 1004, 1010, 1008]
        fichier = tmp_path / "scores.txt"
        fichier.write_text(
            "".join(f"2026-01-{n:02d}T00:00:00 {v}\n" for n, v in enumerate(valeurs, 1)),
            encoding="utf-8",
        )

        main.lister_les_scores(str(fichier))
        lignes = capsys.readouterr().out.splitlines()
        affiches = [int(m) for ligne in lignes for m in re.findall(r"\b10\d\d\b", ligne)]
        par_ligne = [len(re.findall(r"\b10\d\d\b", ligne)) for ligne in lignes]

        assert affiches == sorted(valeurs, reverse=True)[:10]
        assert max(par_ligne) == 1

    @pytest.mark.point("dix meilleurs, décroissants, un par ligne")
    @pytest.mark.parametrize(
        "contenu, premier",
        [
            ("2026-01-01T00:00:00 10\n2026-01-02T00:00:00 90\n", "90"),
            ("2026-01-01T00:00:00 500\n2026-01-02T00:00:00 500\n", "500"),
            ("2026-01-01T00:00:00 7\n", "7"),
        ],
    )
    def test_classement_des_scores(self, tmp_path, capsys, contenu, premier):
        """lister_les_scores affiche le meilleur score en premier."""

        fichier = tmp_path / "scores.txt"
        fichier.write_text(contenu, encoding="utf-8")

        main.lister_les_scores(str(fichier))
        affichage = capsys.readouterr().out

        assert premier in affichage.splitlines()[1]

    @pytest.mark.point("dix meilleurs, décroissants, un par ligne")
    def test_fichier_absent(self, tmp_path, capsys):
        """Sans fichier de scores, lister_les_scores affiche un message au lieu de planter."""

        main.lister_les_scores(str(tmp_path / "absent.txt"))

        assert capsys.readouterr().out.strip() != ""

"""Tests automatiques de la phase 2 — exemple.

Comme ceux de la phase 1, ces tests s'exécutent **sans fenêtre graphique et
sans son** : `conftest.py` remplace les deux modules concernés par des
doublures. Vous pouvez donc les lancer autant de fois que vous voulez, même
pendant que le jeu tourne :

    python3 -m pytest tests/ -v

Un test par comportement attendu, dans l'ordre des étapes de l'énoncé. Tant
qu'une étape n'est pas écrite, son test échoue : c'est normal, et c'est la
liste de ce qu'il vous reste à faire.
"""

import pathlib

import pytest

import main
from .aides import (
    analyser,
    creer_paxman,
    paxman_lance,
    placer_paxman_sur,
    plateau_en_couloirs,
    rendre_dangereux,
    tuile_d_une_pilule_simple,
    tuile_de_la_pilule_de_force,
    tuiles_des_pilules,
    vider_le_plateau,
)

TRAME = 1 / 60


def lire_les_scores() -> str:
    """Retourne le contenu du fichier des scores."""

    return pathlib.Path("scores.txt").read_text(encoding="utf-8")


# ------------------------------------------------ ce qui est déjà fourni ---


class TestModeDiagnostic:
    """Vérifie le mode diagnostic (fourni, rien à coder)."""

    def test_diagnostic_demarre(self, creer_jeu):
        """Le jeu se crée en mode diagnostic sans erreur."""

        jeu = creer_jeu(diagnostic=True)

        assert jeu.fenetre.est_programmee(jeu.afficher_sans_animer)
        assert not jeu.fenetre.est_programmee(jeu.animer_le_jeu)

    def test_entete_montre_la_manette(self, creer_jeu):
        """En mode diagnostic, l'entête affiche l'état de la manette et de l'espace."""

        jeu = creer_jeu(diagnostic=True)
        jeu.fenetre.manette = (-1, 0)
        jeu.fenetre.accelerateur = True
        position = jeu.paxman.position

        jeu.afficher_sans_animer(TRAME)

        assert "(-1, 0)" in jeu.fenetre.score.text
        assert "ACCÉLÈRE" in jeu.fenetre.score.text
        assert jeu.paxman.position == position      # rien ne bouge


class TestMouvementFourni:
    """Vérifie le mouvement de la phase 1, déjà écrit dans la coquille (contrôle)."""

    def test_vire_des_que_possible(self):
        """Flèche du haut tenue : Paxman vire à la première ouverture, puis s'arrête au mur."""

        plateau = plateau_en_couloirs()
        paxman = paxman_lance()

        for _ in range(120):
            paxman.deplacer((0, 1), TRAME, plateau)

        assert paxman.position == pytest.approx((4, 4))

    def test_les_fantomes_bougent(self, jeu):
        """Une fois les portes ouvertes, les quatre fantômes se déplacent."""

        jeu.ouvrir_les_portes(0)
        departs = {nom: fantome.position for nom, fantome in jeu.fantomes.items()}

        for _ in range(60):
            jeu.animer_le_jeu(TRAME)

        immobiles = [nom for nom, depart in departs.items() if jeu.fantomes[nom].position == depart]

        assert not immobiles, f"fantômes restés immobiles : {immobiles}"


class TestRecolteFournie:
    """Vérifie la récolte de la phase 1, déjà écrite dans la coquille (contrôle)."""

    def test_pilule_ramassee(self, jeu):
        """Passer sur une pilule la retire du plateau et ajoute 10 points au score."""

        tuile = tuile_d_une_pilule_simple(jeu)
        placer_paxman_sur(jeu, tuile)

        jeu.animer_le_jeu(TRAME)

        assert jeu.paxman.score == 10
        assert jeu.plateau.recompense_a(tuile) is None
        assert "10" in jeu.fenetre.score.text


# ------------------------------------------- étape 1 : la pilule de force ---


class TestPiluleDeForce:
    """Vérifie l'effet d'une pilule de force (étape 1)."""

    def test_les_fantomes_prennent_peur(self, jeu):
        """Après une pilule de force, les quatre fantômes passent en mode « fuite »."""

        jeu.appliquer_la_pilule_force()

        modes = {f.nom: f.mode for f in jeu.fantomes.values()}

        assert set(modes.values()) == {"fuite"}, f"modes des fantômes : {modes}"

    def test_paxman_accelere(self, jeu):
        """Après une pilule de force, Paxman prend la vitesse du réglage « vitesse-force »."""

        jeu.appliquer_la_pilule_force()

        assert jeu.paxman.vitesse == jeu.paxman.reglage("vitesse-force")

    def test_fin_effet_programmee(self, jeu):
        """L'effet d'une pilule de force est programmé pour s'arrêter après « fuite-durée »."""

        jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.delai_de(jeu.terminer_effet_pilule_force) == pytest.approx(
            jeu.reglage("fuite-durée")
        )

    def test_avertissement_programme(self, jeu):
        """Le clignotement de fin de vulnérabilité est programmé à 80 % de « fuite-durée »."""

        jeu.appliquer_la_pilule_force()

        assert jeu.fenetre.delai_de(jeu.signaler_fin_vulnerabilite) == pytest.approx(
            0.8 * jeu.reglage("fuite-durée")
        )

    def test_seconde_pilule_relance(self, jeu):
        """Une deuxième pilule de force annule le minuteur de la première et le relance."""

        jeu.appliquer_la_pilule_force()
        jeu.appliquer_la_pilule_force()

        # un seul minuteur subsiste, et il porte de nouveau la durée complète
        assert jeu.fenetre.nombre_de_minuteurs(jeu.terminer_effet_pilule_force) == 1
        assert jeu.fenetre.delai_de(jeu.terminer_effet_pilule_force) == pytest.approx(
            jeu.reglage("fuite-durée")
        )

    def test_pilule_ramassee_en_jeu(self, jeu):
        """Passer sur une pilule de force rapporte 100 points et déclenche son effet."""

        placer_paxman_sur(jeu, tuile_de_la_pilule_de_force(jeu))

        jeu.animer_le_jeu(TRAME)

        assert jeu.paxman.score == 100
        modes = {f.nom: f.mode for f in jeu.fantomes.values()}
        assert set(modes.values()) == {"fuite"}, f"modes des fantômes : {modes}"

    def test_fin_effet_dangereux(self, jeu):
        """À la fin de l'effet, les fantômes quittent le mode « fuite » et Paxman ralentit."""

        jeu.appliquer_la_pilule_force()
        jeu.terminer_effet_pilule_force(0)

        assert jeu.paxman.vitesse == jeu.paxman.reglage("vitesse-défaut")
        fuyards = [f.nom for f in jeu.fantomes.values() if f.mode == "fuite"]
        assert not fuyards, f"fantômes encore en fuite : {fuyards}"


# ----------------------------------------- étape 2 : dévorer un fantôme ----


class TestDevorerUnFantome:
    """Vérifie la dévoration d'un fantôme et le combo (étape 2)."""

    def test_fantome_en_fuite_200(self, jeu, fantome):
        """Le premier fantôme dévoré après une pilule de force vaut 200 points."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)

        assert jeu.paxman.score == 200

    def test_devore_devient_revenant(self, jeu, fantome):
        """Un fantôme dévoré passe en mode « revenant » et retourne à la cage."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)

        assert fantome.mode == "revenant"

    def test_revenant_inoffensif(self, jeu, fantome):
        """Toucher un fantôme déjà dévoré (« revenant ») ne coûte pas de vie."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)
        vies = jeu.paxman.vies

        assert jeu.traiter_la_collision(fantome) is False
        assert jeu.paxman.vies == vies

    def test_la_trame_continue(self, jeu, fantome):
        """Dévorer un fantôme ne met pas fin à la trame : traiter_la_collision retourne False."""

        jeu.appliquer_la_pilule_force()

        assert jeu.traiter_la_collision(fantome) is False

    def test_le_combo_double(self, jeu):
        """Les quatre fantômes d'une même pilule valent 200, 400, 800 puis 1600 points."""

        jeu.appliquer_la_pilule_force()

        gains = []
        for fantome in jeu.fantomes.values():
            avant = jeu.paxman.score
            jeu.traiter_la_collision(fantome)
            gains.append(jeu.paxman.score - avant)

        assert gains == [200, 400, 800, 1600]

    def test_le_combo_repart_a_200(self, jeu):
        """Chaque nouvelle pilule de force fait repartir le combo à 200 points."""

        jeu.appliquer_la_pilule_force()
        for fantome in jeu.fantomes.values():
            jeu.traiter_la_collision(fantome)

        jeu.appliquer_la_pilule_force()
        avant = jeu.paxman.score
        jeu.traiter_la_collision(next(iter(jeu.fantomes.values())))

        assert jeu.paxman.score - avant == 200

    def test_fantome_dangereux_mortel(self, jeu, fantome):
        """Hors de l'effet d'une pilule, toucher un fantôme coûte une vie."""

        rendre_dangereux(jeu)
        vies = jeu.paxman.vies

        jeu.traiter_la_collision(fantome)

        assert jeu.paxman.vies == vies - 1


# ---------------------------------------------------- étape 3 : les vies ---


class TestLesVies:
    """Vérifie la gestion des vies (étape 3)."""

    def test_vies_initiales(self, jeu):
        """Paxman démarre la partie avec le nombre de vies prévu par le niveau."""

        assert jeu.paxman.vies == jeu.paxman.reglage("vies")

    def test_collision_coute_une_vie(self, jeu):
        """Une collision fatale retire une vie, sans mettre fin à la partie."""

        jeu.perdre_une_vie()

        assert jeu.paxman.vies == jeu.paxman.reglage("vies") - 1

    def test_la_trame_s_arrete(self, jeu):
        """Perdre une vie met fin à la trame en cours : perdre_une_vie retourne True."""

        assert jeu.perdre_une_vie() is True

    def test_la_partie_se_fige(self, jeu):
        """Après la perte d'une vie, la partie est mise en pause (affichage de READY!)."""

        jeu.perdre_une_vie()

        assert jeu.en_pause, "la partie n'est pas en pause"

    def test_pause_fige_le_jeu(self, jeu):
        """Pendant la pause, animer_le_jeu ne déplace plus Paxman."""

        jeu.perdre_une_vie()
        position = jeu.paxman.position
        jeu.animer_le_jeu(TRAME)

        assert jeu.paxman.position == position

    def test_retour_au_depart(self, jeu):
        """Après la perte d'une vie, Paxman est replacé à sa position initiale."""

        jeu.paxman.position = (1.0, 1.0)
        jeu.perdre_une_vie()

        assert jeu.paxman.position == tuple(jeu.paxman.reglage("position-initiale"))

    def test_recompenses_conservees(self, jeu):
        """Perdre une vie ne remet pas les récompenses déjà ramassées sur le plateau."""

        jeu.plateau.ramasser(tuiles_des_pilules(jeu)[0])
        restantes = jeu.plateau.compter_recompenses()

        jeu.perdre_une_vie()

        assert jeu.plateau.compter_recompenses() == restantes

    def test_derniere_vie_fin_partie(self, jeu):
        """Quand la dernière vie est perdue, la partie se termine par StopIteration."""

        jeu.paxman.vies = 1

        with pytest.raises(StopIteration):
            jeu.perdre_une_vie()


# ------------------------------------------------- étape 4 : la victoire ---


class TestLaVictoire:
    """Vérifie la détection de la victoire (étape 4)."""

    def test_plateau_vide_victoire(self, jeu):
        """Quand la dernière récompense est ramassée, la partie se termine par StopIteration."""

        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

    def test_continue_si_une_pilule(self, jeu):
        """Tant qu'il reste une seule récompense, la partie continue."""

        vider_le_plateau(jeu, sauf=1)

        jeu.animer_le_jeu(TRAME)  # ne doit rien lever

        assert jeu.plateau.compter_recompenses() == 1

    def test_entete_score_et_vies(self, jeu):
        """L'entête de la fenêtre affiche le score courant et le nombre de vies."""

        jeu.paxman.score = 1850
        jeu.animer_le_jeu(TRAME)

        assert "1850" in jeu.fenetre.score.text
        assert str(jeu.paxman.vies) in jeu.fenetre.score.text


# --------------------------------------------------- étape 5 : les sons ---


class TestLesSons:
    """Vérifie le déclenchement des sons (étape 5)."""

    def test_sirene_au_demarrage(self, sons):
        """La sirène d'arrière-plan est lancée dès la création de la partie."""

        assert sons["sirène"].joue >= 1

    def test_son_pilule_ramassee(self, jeu, sons):
        """Ramasser une récompense joue le son « mange-pilule »."""

        placer_paxman_sur(jeu, tuile_d_une_pilule_simple(jeu))

        jeu.ramasser_la_recompense()

        assert sons["mange-pilule"].joue == 1

    def test_pilule_change_musique(self, jeu, sons):
        """Une pilule de force arrête la sirène et lance « fantômes-enfuite »."""

        jeu.appliquer_la_pilule_force()

        assert sons["sirène"].arrete >= 1
        assert sons["fantômes-enfuite"].joue >= 1

    def test_son_fantome_devore(self, jeu, fantome, sons):
        """Dévorer un fantôme joue le son « mange-fantôme »."""

        jeu.appliquer_la_pilule_force()
        jeu.traiter_la_collision(fantome)

        assert sons["mange-fantôme"].joue == 1

    def test_requiem_vie_perdue(self, jeu, sons):
        """Perdre une vie arrête les sons en cours et joue « paxman-requiem »."""

        jeu.perdre_une_vie()

        assert sons["paxman-requiem"].joue == 1
        assert sons["sirène"].arrete >= 1

    def test_victoire_coupe_les_sons(self, jeu, sons):
        """Une partie gagnée arrête tous les sons."""

        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

        en_lecture = [nom for nom, lecteur in sons.items() if lecteur.en_lecture()]

        assert not en_lecture, f"sons encore en lecture : {en_lecture}"


# --------------------------------------- étape 6 : la sauvegarde du score ---


class TestLaSauvegardeDesScores:
    """Vérifie l'écriture du fichier des scores (étape 6)."""

    def test_le_fichier_est_cree(self, jeu):
        """La fin d'une partie crée le fichier scores.txt."""

        jeu.sauvegarder_score()

        assert pathlib.Path("scores.txt").exists(), "scores.txt n'a pas été créé"

    def test_ligne_date_et_score(self, jeu):
        """Chaque ligne du fichier contient un horodatage, une espace et le score."""

        jeu.paxman.score = 1850
        jeu.sauvegarder_score()

        horodatage, score = lire_les_scores().split()

        assert score == "1850"
        assert horodatage.count("-") == 2 and "T" in horodatage

    def test_les_parties_s_ajoutent(self, jeu):
        """Une nouvelle partie s'ajoute au fichier sans effacer les précédentes."""

        jeu.paxman.score = 100
        jeu.sauvegarder_score()
        jeu.paxman.score = 200
        jeu.sauvegarder_score()

        assert lire_les_scores().split()[1::2] == ["100", "200"]

    def test_defaite_enregistree(self, jeu):
        """Une partie perdue enregistre le score avant de se terminer."""

        jeu.paxman.vies = 1
        jeu.paxman.score = 420

        with pytest.raises(StopIteration):
            jeu.perdre_une_vie()

        assert "420" in lire_les_scores()

    def test_victoire_enregistree(self, jeu):
        """Une partie gagnée enregistre elle aussi le score."""

        jeu.paxman.score = 9999
        vider_le_plateau(jeu)

        with pytest.raises(StopIteration):
            jeu.animer_le_jeu(TRAME)

        assert "9999" in lire_les_scores()


# -------------------------------------------- étape 7 : ligne de commande ---


class TestLaLigneDeCommande:
    """Vérifie les options ajoutées à main.py (étape 7)."""

    def test_sourdine_existe(self, monkeypatch):
        """L'option --sourdine est reconnue et vaut False par défaut."""

        assert analyser(monkeypatch, []).sourdine is False
        assert analyser(monkeypatch, ["--sourdine"]).sourdine is True

    def test_sourdine_forme_courte(self, monkeypatch):
        """L'option --sourdine a aussi une forme courte -s."""

        assert analyser(monkeypatch, ["-s"]).sourdine is True

    def test_lister_scores_existe(self, monkeypatch):
        """L'option --lister-scores est reconnue, en forme longue comme en forme courte."""

        assert analyser(monkeypatch, []).lister_scores is False
        assert analyser(monkeypatch, ["--lister-scores"]).lister_scores is True
        assert analyser(monkeypatch, ["-l"]).lister_scores is True

    def test_options_phase_1(self, monkeypatch):
        """Les options --niveau et --diagnostic de la phase 1 fonctionnent toujours."""

        arguments = analyser(monkeypatch, ["-n", "1", "-d"])

        assert arguments.niveau == 1 and arguments.diagnostic is True

    def test_lister_scores_classement(self, tmp_path, capsys):
        """lister_les_scores affiche les scores du plus grand au plus petit."""

        fichier = tmp_path / "scores.txt"
        fichier.write_text(
            "2026-03-20T10:00:00 300\n2026-03-20T11:00:00 1200\n", encoding="utf-8"
        )

        main.lister_les_scores(str(fichier))
        affichage = capsys.readouterr().out

        assert affichage.index("1200") < affichage.index("300")

    def test_lister_scores_sans_fichier(self, tmp_path, capsys):
        """Sans fichier de scores, lister_les_scores le dit au lieu de planter."""

        main.lister_les_scores(str(tmp_path / "absent.txt"))

        assert capsys.readouterr().out.strip() != ""


# ------------------------------------- étape 8 : la jauge d'accélération ---


class TestLaJauge:
    """Vérifie la jauge d'accélération (étape 8).

    Les premiers tests sont des tests **unitaires** : ils créent un Paxman
    seul, sans partie ni fenêtre, et vérifient une seule méthode à la fois.
    """

    def test_jauge_pleine_au_depart(self):
        """Un Paxman neuf a une jauge pleine (1.0)."""

        assert creer_paxman().jauge == pytest.approx(1.0)

    def test_accelerer_vide_la_jauge(self):
        """Accélérer pendant 0,5 s avec « jauge-vidange » = 0,5 retire 0,25 à la jauge."""

        paxman = creer_paxman()

        permis = paxman.mettre_a_jour_la_jauge(True, 0.5)

        assert permis is True
        assert paxman.jauge == pytest.approx(0.75)

    def test_relacher_remplit_la_jauge(self):
        """Relâcher pendant 1 s avec « jauge-recharge » = 0,2 ajoute 0,2 à la jauge."""

        paxman = creer_paxman()
        paxman.jauge = 0.5

        permis = paxman.mettre_a_jour_la_jauge(False, 1.0)

        assert permis is False
        assert paxman.jauge == pytest.approx(0.7)

    def test_jauge_plafonnee_a_1(self):
        """La jauge ne dépasse jamais 1, même après une longue recharge."""

        paxman = creer_paxman()
        paxman.jauge = 0.95

        paxman.mettre_a_jour_la_jauge(False, 10.0)

        assert paxman.jauge == pytest.approx(1.0)

    def test_jauge_jamais_negative(self):
        """La jauge ne descend jamais sous 0, même après une longue accélération."""

        paxman = creer_paxman()
        paxman.jauge = 0.1

        paxman.mettre_a_jour_la_jauge(True, 10.0)

        assert paxman.jauge == pytest.approx(0.0)

    def test_jauge_vide_bloque(self):
        """Jauge vide et touche enfoncée : pas d'accélération, et la jauge reste vide."""

        paxman = creer_paxman()
        paxman.jauge = 0.0

        permis = paxman.mettre_a_jour_la_jauge(True, 1.0)

        assert permis is False
        assert paxman.jauge == pytest.approx(0.0)

    def test_jeu_sans_jauge_ralentit(self, jeu):
        """Dans la partie, une jauge vide empêche l'espace d'accélérer Paxman."""

        jeu.paxman.jauge = 0.0
        jeu.fenetre.accelerateur = True

        jeu.ajuster_acceleration(0.2)

        assert jeu.paxman.facteur == pytest.approx(1.0)

    def test_jeu_avec_jauge_accelere(self, jeu):
        """Dans la partie, une jauge pleine laisse l'espace accélérer Paxman."""

        jeu.fenetre.accelerateur = True

        jeu.ajuster_acceleration(0.2)

        assert jeu.paxman.facteur > 1.0
        assert jeu.paxman.jauge < 1.0

    def test_entete_montre_la_jauge(self, jeu):
        """L'entête change selon que la jauge est pleine ou vide (format libre)."""

        jeu.animer_le_jeu(TRAME)
        pleine = jeu.fenetre.score.text

        jeu.paxman.jauge = 0.0
        jeu.animer_le_jeu(TRAME)
        vide = jeu.fenetre.score.text

        assert pleine != vide, f"l'entête ne change pas avec la jauge : {pleine!r}"

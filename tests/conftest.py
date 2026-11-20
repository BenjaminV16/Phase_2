"""Configuration commune des tests — FOURNI, rien à modifier.

Ce fichier est lu par pytest avant tout fichier de test. Il y installe les
doublures de `factices.py`, ce qui permet aux tests de la phase 2 de créer un
vrai `JeuPaxman` sans ouvrir de fenêtre ni jouer de son.
"""

import importlib

import pytest

from . import factices

factices.installer()


@pytest.fixture(name="creer_jeu")
def fixture_creer_jeu(tmp_path, monkeypatch):
    """Fabrique de parties, dans un dossier temporaire.

    Le dossier temporaire sert à `scores.txt` : les tests n'écrivent donc
    jamais dans votre dossier de projet. Le jeu n'est importé qu'ici, une fois
    les doublures en place.
    """

    module_jeu = importlib.import_module("paxman.jeu")
    monkeypatch.chdir(tmp_path)

    def creer(diagnostic=False):
        return module_jeu.JeuPaxman(niveau=1, diagnostic=diagnostic, sourdine=True)

    return creer


@pytest.fixture(name="jeu")
def fixture_jeu(creer_jeu):
    """Une partie neuve."""

    return creer_jeu()


@pytest.fixture(name="fantome")
def fixture_fantome(jeu):
    """Le premier fantôme de la partie."""

    return next(iter(jeu.fantomes.values()))


@pytest.fixture(name="sons")
def fixture_sons(jeu):
    """Les lecteurs de sons de la partie, qui notent ce qu'on leur demande."""

    del jeu  # la partie doit exister : c'est elle qui charge les sons
    return factices.SONS

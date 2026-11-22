"""Ce module contient le code principal du jeu Paxman."""

import argparse
from ast import arguments

FICHIER_SCORES = "scores.txt"


def lister_les_scores(
    fichier: str | None = None, nombre: int = 10
) -> None:
    """Affiche les meilleurs scores, du plus grand au plus petit."""
    if fichier is None:
        fichier = FICHIER_SCORES

    try:
        with open(fichier, encoding="utf-8") as f:
            lignes = [ligne.strip() for ligne in f if ligne.strip()]
    except FileNotFoundError:
        print("Aucun score enregistré.")
        return

    lignes = sorted(
        lignes, key=lambda ligne: int(ligne.split()[1]), reverse=True
    )

    print(f"Meilleurs scores ({min(nombre, len(lignes))}) :")
    for ligne in lignes[:nombre]:
        print(ligne)


def analyser_ligne_commande() -> argparse.Namespace:
    """Analyse les arguments de la ligne de commande."""

    analyseur = argparse.ArgumentParser(description="Le jeu de Paxman.")

    analyseur.add_argument(
        "-n",
        "--niveau",
        type=int,
        default=1,
        help="numéro du niveau à charger (défaut : 1)",
    )

    analyseur.add_argument(
        "-d",
        "--diagnostic",
        action="store_true",
        help="affiche le jeu sans l'animer et montre l'état de la manette",
    )

    analyseur.add_argument(
        "-s",
        "--sourdine",
        action="store_true",
        help="désactive tous les sons du jeu",
    )

    analyseur.add_argument(
        "-l",
        "--lister-scores",
        action="store_true",
        help="affiche les 10 meilleurs scores, puis quitte",
    )

    return analyseur.parse_args()


if __name__ == "__main__":
    # analyser la ligne de commande
    arguments = analyser_ligne_commande()

    if arguments.lister_scores:
        lister_les_scores()
        raise SystemExit

    # Le jeu n'est importé qu'ici, et non en haut du fichier : importer
    # `paxman.jeu` entraîne l'ouverture de l'environnement graphique, ce qui
    # serait inutile — et parfois impossible, par exemple en ligne de commande
    # sans écran — pour une option qui ne fait qu'afficher du texte.
    from paxman.jeu import JeuPaxman

    # instancier le jeu de Paxman
    jeu = JeuPaxman(
        niveau=arguments.niveau,
        diagnostic=arguments.diagnostic,
        sourdine=arguments.sourdine,
    )

    # démarrer la boucle événementielle du jeu
    jeu.demarrer_boucle_evenements()

"""Paquet du jeu Paxman.

Ce fichier ne contient volontairement que de la syntaxe très ancienne : il est
le premier module chargé, donc le seul endroit où l'on peut détecter une version
de Python trop vieille *avant* que l'interpréteur ne bute sur une syntaxe
moderne (`match`, annotations `int | float`, ...) avec un `SyntaxError` obscur.
"""

import sys

# en dessous, le code du projet ne se compile même pas (`match`, `X | Y`)
VERSION_MINIMALE = (3, 10)

# la version demandée par le cours
VERSION_RECOMMANDEE = (3, 12)


def _version(numeros):
    return ".".join(str(n) for n in numeros)


if sys.version_info < VERSION_MINIMALE:
    raise SystemExit(
        "\n"
        "  Votre version de Python est trop ancienne pour ce projet.\n"
        "\n"
        "      requis    : Python " + _version(VERSION_RECOMMANDEE) + " ou plus récent\n"
        "      vous avez : Python " + _version(sys.version_info[:3]) + "\n"
        "      chemin    : " + sys.executable + "\n"
        "\n"
        "  Sur macOS, la commande `python3` désigne souvent le Python livré avec\n"
        "  les outils de développement d'Apple, qui est trop vieux. Installez une\n"
        "  version récente depuis https://www.python.org/downloads/ puis relancez\n"
        "  en nommant explicitement cette version, par exemple :\n"
        "\n"
        "      python3.12 -m pip install -r requirements.txt\n"
        "      python3.12 main.py\n"
        "\n"
        "  La commande `python3 --version` vous indique laquelle est utilisée par\n"
        "  défaut, et `which -a python3` (macOS, Linux) les liste toutes.\n"
    )

if sys.version_info < VERSION_RECOMMANDEE:
    print(
        "Attention : le cours demande Python "
        + _version(VERSION_RECOMMANDEE)
        + " ou plus récent ; vous utilisez "
        + _version(sys.version_info[:3])
        + ".",
        file=sys.stderr,
    )

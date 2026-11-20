# PAXMAN — phase 2 : et si on rendait le jeu vivant…

À la fin de la phase 1, votre Paxman se déplaçait, mangeait les pilules et
mourait au premier contact d'un fantôme. Cette **coquille** reprend exactement
ce point de départ : la phase 1 y est terminée, et le jeu se joue déjà.

Votre tâche, en phase 2, est de transformer cette démonstration en un vrai
jeu&puncsp;: des pilules de force qui font fuir les fantômes, des vies, une
victoire, des sons, des scores enregistrés et une accélération qui se mérite.
Le travail se découpe en **huit étapes**, décrites dans l'énoncé&puncsp;:

| Étape | Ce que vous écrivez                           | Où                                  |
| :---: | :-------------------------------------------- | :---------------------------------- |
|   1   | l'effet d'une pilule de force                 | `paxman/jeu.py`                     |
|   2   | dévorer un fantôme, et le combo 200 → 1600    | `paxman/jeu.py`                     |
|   3   | les vies, `READY!` et la pause                | `paxman/jeu.py`, `paxman/paxman.py` |
|   4   | la victoire                                   | `paxman/jeu.py`                     |
|   5   | les sons                                      | `paxman/jeu.py`                     |
|   6   | la sauvegarde des scores                      | `paxman/jeu.py`                     |
|   7   | les options `--sourdine` et `--lister-scores` | `main.py`                           |
|   8   | la jauge d'accélération                       | `paxman/paxman.py`, `paxman/jeu.py` |

Chaque endroit à compléter est marqué d'un commentaire `TODO (phase 2, étape N)`.

# Mise en route

1. Installez la **version 3.12 ou plus récente** de Python (voir FAQ).
2. Installez **Git** (voir FAQ).
3. Créez votre dépôt à partir de la coquille, puis clonez-le.
4. Installez les dépendances et lancez le jeu&puncsp;:

```bash
pip install -r requirements.txt
python3 main.py
```

> **Avant tout, vérifiez votre version de Python&puncsp;:** `python3 --version`.
>
> Si la réponse est 3.9 ou 3.10, vous utilisez le Python livré avec votre
> système. C'est le cas par défaut sur **macOS**, où `python3` désigne celui des
> outils de développement d'Apple. Le projet ne démarrera pas : il utilise des
> nouveautés du langage que ces versions ne comprennent pas.
>
> Installez une version récente depuis <https://www.python.org/downloads/>, puis
> **nommez-la explicitement** dans toutes vos commandes&puncsp;:
>
> ```bash
> python3.12 -m pip install -r requirements.txt
> python3.12 main.py
> ```
>
> `which -a python3` (macOS, Linux) liste toutes les versions installées. Notez
> que `pip` installe les bibliothèques dans la version de Python à laquelle il
> est rattaché&puncsp;: si vous changez de version, refaites l'installation des
> dépendances avec celle-ci. C'est vrai aussi pour `pytest` et `pylint`.

Une fenêtre s'ouvre, et **le jeu se joue** : Paxman répond aux flèches, la
barre d'espace l'accélère, il mange les pilules et son score s'affiche en haut
de la fenêtre&puncsp;:

```text
Score: 0
```

Les quatre fantômes sortent de la cage au bout de 5 secondes et le
pourchassent. Pour l'instant, le premier contact termine la partie, et une
pilule de force ne rapporte que ses 100 points&puncsp;: c'est ce que vous allez
changer.

Le jeu joue aussi des sons, rangés dans le dossier `sons/`. Si vous travaillez
dans un endroit où ils dérangent, coupez-les&puncsp;; l'option `--sourdine` est
justement à écrire à l'étape 7.

## Le mode diagnostic

L'affichage de la manette de la phase 1 est toujours là&puncsp;:

```bash
python3 main.py --diagnostic
```

Rien ne bouge, et l'entête affiche, à la place du score, ce que la fenêtre a
compris du clavier&puncsp;:

```text
Manette: (-1, 0)  Espace: ACCÉLÈRE
```

C'est encore le premier réflexe à avoir quand « ça ne bouge plus ».

# Vérifier votre travail

## Les tests, étape par étape

```bash
pytest tests/test_phase2.py
```

Ces tests ne demandent **ni fenêtre ni son** : le fichier `tests/factices.py`
remplace l'affichage et la carte son par des imitations. Vous pouvez donc les
lancer autant de fois que vous voulez, même pendant que le jeu tourne.

Au départ, 10 tests passent et 46 échouent&puncsp;:

- les 10 tests qui passent portent sur ce qui **fonctionne déjà** : le code
  fourni (le mode diagnostic, la sirène au démarrage, les options `--niveau` et
  `--diagnostic`) et le travail de la phase 1 (le mouvement, la récolte, la
  partie qui se termine au contact d'un fantôme).
- les 46 tests qui échouent décrivent, dans l'ordre des étapes, tout ce qu'il
  vous reste à écrire. Leur nom et leur docstring vous disent exactement ce qui
  est attendu.

Pour ne lancer que ceux d'une étape&puncsp;:

```bash
pytest tests/test_phase2.py -k PiluleDeForce -v
pytest tests/test_phase2.py -k LaJauge -v
```

Les tests de la phase 1 (`tests/test_phase1.py`) doivent, eux, **toujours**
passer : ils vérifient que vous n'avez rien cassé.

## Le bilan, critère par critère

```bash
python3 tests/noter_phase2.py
```

Ce script lance tout, en trois temps&puncsp;:

1. les tests de `test_phase2.py`, un par comportement&puncsp;;
2. les tests `test_critere_3.py` à `test_critere_7.py`, qui reprennent les mêmes
   comportements sur beaucoup plus de valeurs, **un fichier par critère de la
   grille d'évaluation**&puncsp;;
3. pylint, sur tout le projet.

Chaque critère est noté **sur 100&puncsp;%** et détaillé en sous-critères,
marqués ✓ (tout passe), ~ (une partie passe) ou ✗ (rien ne passe). Chaque test
raté est expliqué en deux lignes&puncsp;: ce qui était attendu, et ce que votre
code a produit.

Au départ, tous les critères sont à 0&puncsp;%. Le bilan se termine par deux
**contrôles**, qui ne comptent dans aucun critère&puncsp;: le mouvement et la
récolte de la phase 1 doivent rester « intact ». S'ils affichent « CASSÉ »,
réparez-les avant tout le reste.

Pour un bilan plus rapide, sans pylint&puncsp;:

```bash
python3 tests/noter_phase2.py --sans-pylint
```

## Le style : pylint

```bash
python3 -m pylint main.py paxman tests outils
```

**Au départ, la coquille obtient 9,96/10.** Les 8 messages sont tous des
`fixme`&puncsp;: ce sont les commentaires `TODO` qui marquent le travail à
faire. Effacez chacun d'eux une fois son étape terminée&puncsp;: ils ne
disparaissent pas tout seuls. Le travail remis doit obtenir **10/10**.

## Vérifier tous les tests

```bash
pytest -v
```

vérifie tous vos tests.

> [!CAUTION]
> Il est important d'utiliser `python3 tests/noter_phase2.py` et non seulement
> `pytest` de manière à obtenir le bilan par critère. Si vous utilisez seulement
> `pytest`, vous ne verrez que le résultat produit par les tests, et non votre
> bilan.

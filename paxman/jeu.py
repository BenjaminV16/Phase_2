"""Ce module contient la définition de la classe qui encapsule toutes les composantes
du jeu de Paxman.
"""
from datetime import datetime
import json
import pathlib

import pyglet

from .fantome import Fantome
from .fenetre_pyglet import Fenetre
from .obstacles import Porte
from .paxman import Paxman
from .plateau import Plateau
from .recompenses import PiluleForce
from .son_pyglet import charger_les_sons


# TODO (phase 2, étapes 3 et 6) : importer aussi `arreter_tous` du module
# son_pyglet, et la classe `datetime` du module datetime.


class JeuPaxman:
    """Classe qui encapsule les composantes du jeu Paxman.

    Ces composantes sont:
    1. le plateau de jeu;
    2. le Paxman;
    3. la liste de fantômes;
    4. la fenêtre graphique du jeu;
    5. et réglages du jeu.
    """

    # JeuPaxman orchestre tout le jeu (plateau, acteurs, fenêtre, sons et
    # minuteurs) : le découper en plusieurs classes rendrait le projet plus
    # difficile à suivre qu'il ne le simplifierait.
    # pylint: disable=too-many-instance-attributes,too-many-public-methods

    def __init__(self, niveau: int, diagnostic: bool = False,
                 sourdine: bool = False) -> None:
        # déterminer le chemin du fichier des réglages pour le niveau demandé
        path = pathlib.Path(__file__).parent / "niveaux" / f"niveau{niveau}.json"

        # ouvrir le fichier de niveau et lire son contenu
        with path.open("r", encoding="utf-8") as fichier:
            config = json.load(fichier)

        # mémoriser les réglages du jeu
        self._reglages = config["réglages"]

        # initialiser le plateau de jeu
        self._plateau = Plateau(description=config["plateau"])

        # créer le Paxman
        self._paxman = Paxman(
            *config["paxman"]["position-initiale"],
            reglages=config["paxman"],
        )

        # créer les fantômes
        self._fantomes = {}
        for reglages in config["fantômes"]:
            # ajouter le fantôme au dictionnaire de fantômes
            self._fantomes[reglages["nom"]] = Fantome(
                *reglages["position-initiale"],
                reglages=reglages,
            )

        # initialiser la fenêtre d'affichage
        self._fenetre = Fenetre(self.plateau, self._reglages, caption="Jeu de Paxman")

        # charger les sons du jeu (fourni)
        self._sons = charger_les_sons(sourdine=sourdine)

        # programmer l'appel de la méthode d'animation du jeu
        # (en mode diagnostic, on se contente d'afficher le jeu sans l'animer)
        self.fenetre.programmer_appel_fonction(
            self.afficher_sans_animer if diagnostic else self.animer_le_jeu,
            1 / 60,
            intervalle=True,
        )

        # programmer l'ouverture automatique des portes
        self.fenetre.programmer_appel_fonction(
            self.ouvrir_les_portes,
            self._reglages["porte-délai-ouverture"],
        )

        # valeur du prochain fantôme dévoré, doublée à chaque fantôme
        self.combo = 200

        # une partie en pause n'est plus animée (affichage de READY!)
        self._en_pause = False

        # démarrer la sirène d'arrière-plan
        self._sons["sirène"].jouer()

        # passer en mode dispersion
        self.mode = None
        self.alterner_dispersion_poursuite(0)

    @property
    def fenetre(self) -> Fenetre:
        """Retourne la fenêtre graphique de ce jeu."""

        return self._fenetre

    @property
    def fantomes(self) -> dict[str, Fantome]:
        """Retourne les fantômes de ce jeu, sous la forme d'un dictionnaire indexé
        par le nom du fantôme."""

        return self._fantomes

    @property
    def paxman(self) -> Paxman:
        """Retourne le Paxman de ce jeu."""

        return self._paxman

    @property
    def plateau(self) -> Plateau:
        """Retourne le plateau de ce jeu."""

        return self._plateau

    @property
    def manette(self) -> tuple[int, int]:
        """Retourne la direction actuelle de la manette de jeu."""

        return self.fenetre.manette

    @property
    def accelerateur(self) -> bool:
        """Retourne True tant que la touche espace est enfoncée."""

        return self.fenetre.accelerateur

    def reglage(self, titre: str) -> int | float | str | tuple | list:
        """Retourne le réglage associé au titre spécifié."""

        return self._reglages[titre]

    def afficher_sans_animer(self, _delta_t: float | None = None) -> None:
        """Affiche le jeu sans l'animer et montre l'état de la manette (fourni).

        Appelée 60 fois par seconde en mode diagnostic (`python3 main.py -d`),
        à la place de `animer_le_jeu`. Rien ne bouge : Paxman et les fantômes
        restent à leur position de départ, et l'entête affiche, à la place du
        score, ce que la fenêtre a compris du clavier.
        """

        self.fenetre.dessiner_paxman(self.paxman)
        for fantome in self.fantomes.values():
            self.fenetre.dessiner_fantome(fantome)

        espace = "ACCÉLÈRE" if self.accelerateur else "relâchée"
        self.fenetre.score.text = f"Manette: {self.manette}    Espace: {espace}"

    # distance en deçà de laquelle Paxman et un fantôme se touchent
    CONTACT = 0.5

    def animer_le_jeu(self, delta_t: float | None = None) -> None:
        """Anime une trame de jeu.

        Cette version est celle de la **phase 1** : elle est complète, et vous
        servez de point de départ pour la phase 2. Les endroits à compléter
        portent un commentaire `TODO`.
        """

        delta_t = delta_t if delta_t is not None else 1 / 60

        if self.en_pause:
            # la partie est figée (affichage de READY!) : rien à animer
            return

        # 1-2. la manette, l'accélération, puis le déplacement de Paxman
        self.ajuster_acceleration(delta_t)
        self.paxman.deplacer(self.manette, delta_t, self.plateau)
        self.fenetre.dessiner_paxman(self.paxman)

        # 3. la récompense qui se trouve sous Paxman
        self.ramasser_la_recompense()

        # 4-5. les fantômes, et ce qui arrive lorsqu'ils touchent Paxman
        for fantome in self.fantomes.values():
            direction = fantome.choisir_une_direction(self)
            fantome.deplacer(direction, delta_t, self.plateau)
            self.fenetre.dessiner_fantome(fantome)

            if self.paxman.calculer_distance_l1(fantome.position) < self.CONTACT:
                if self.traiter_la_collision(fantome):
                    return

        if self.plateau.partie_gagnee():
            for son in self._sons.values():
                son.arreter()
            self.sauvegarder_score()
            raise StopIteration("Partie gagnée")

        # 6. l'affichage du score, des vies et de la jauge
        self.fenetre.score.text = (
            f"Score: {self.paxman.score}   "
            f"Vies: {self.paxman.vies}   "
            f"Jauge: {int(self.paxman.jauge * 100)}%"
        )

    def ramasser_la_recompense(self) -> None:
        """Ramasse la récompense sous Paxman, s'il y en a une (phase 1)."""

        tuile = self.paxman.tuile_courante()
        recompense = self.plateau.recompense_a(tuile)

        if recompense is None:
            return

        if self.paxman.calculer_distance_l1(tuile) >= self.CONTACT:
            # Paxman n'est pas encore assez proche du centre de la tuile
            return

        # retenir le type AVANT de retirer la récompense du plateau
        est_une_pilule_de_force = isinstance(recompense, PiluleForce)

        self.paxman.score += self.plateau.ramasser(tuile)
        self.fenetre.dessiner_recompenses(self.plateau)

        self.paxman.score += self.plateau.ramasser(tuile)
        self.fenetre.dessiner_recompenses(self.plateau)

        self._sons["mange-pilule"].jouer()

        if est_une_pilule_de_force:
            self.appliquer_la_pilule_force()

        if est_une_pilule_de_force:
            self.appliquer_la_pilule_force()

    def appliquer_la_pilule_force(self) -> None:
        self.fenetre.annuler_appel_fonction(self.terminer_effet_pilule_force)
        self.fenetre.annuler_appel_fonction(self.signaler_fin_vulnerabilite)
        self.fenetre.annuler_appel_fonction(self.alterner_dispersion_poursuite)
        
        #Donner à Paxman la vitesse 
        self.paxman.vitesse = self.paxman.reglage("vitesse-force")

        #Faire passer tous les fantômes en mode fuite
        for fantome in self.fantomes.values():
            fantome.mode = "fuite"

        self.combo = 200

        # Couper la sirène et lancer la musique de fuite
        self._sons["sirène"].arreter()
        self._sons["fantômes-enfuite"].jouer()

        duree = self._reglages["fuite-durée"]
        #effet visuel  
        self.fenetre.programmer_appel_fonction(
            self.signaler_fin_vulnerabilite, 0.8 * duree
        )
        #Retour normal
        self.fenetre.programmer_appel_fonction(
           self.terminer_effet_pilule_force, duree
        )

    def traiter_la_collision(self, fantome: Fantome) -> bool:
        """Traite la collision entre Paxman et un fantôme."""

        if fantome.mode == "fuite":
            self.paxman.score += self.combo
            self.combo *= 2
            fantome.mode = "revenant"
            self._sons["mange-fantôme"].jouer()
            return False

        if fantome.mode == "revenant":
            return False

        return self.perdre_une_vie()


    def perdre_une_vie(self) -> bool:
        """Retire une vie à Paxman et relance la partie, ou y met fin.

        Retourne True si la trame doit s'arrêter là.
        """
        self.paxman.vies -= 1

        for son in self._sons.values():
            son.arreter()
        self._sons["paxman-requiem"].jouer()

        if self.paxman.vies <= 0:
            self.sauvegarder_score()
            raise StopIteration("Partie perdue")

        self.replacer_les_acteurs()
        self.fenetre.score.text = "READY!"
        self.mettre_en_pause(2)
        return True


    def sauvegarder_score(self) -> None:
        """Ajoute le score actuel de Paxman à la fin du fichier `scores.txt`."""
        horodatage = datetime.now().isoformat(timespec="seconds")
        with open("scores.txt", "a", encoding="utf-8") as fichier:
            fichier.write(f"{horodatage} {self.paxman.score}\n")

    @property
    def en_pause(self) -> bool:
        """Indique si la partie est momentanément figée (fourni)."""

        return self._en_pause

    def mettre_en_pause(self, duree: float) -> None:
        """Fige la partie pendant `duree` secondes, puis la relance (fourni)."""

        self._en_pause = True
        self.fenetre.annuler_appel_fonction(self.reprendre)
        self.fenetre.programmer_appel_fonction(self.reprendre, duree)

    def reprendre(self, _delta_t: float = 0.0) -> None:
        """Relance la partie après une pause (fourni)."""

        self._en_pause = False

    def replacer_les_acteurs(self) -> None:
        """Remet Paxman et les quatre fantômes à leur position de départ (fourni).

        Les récompenses déjà ramassées, elles, ne reviennent pas : on reprend la
        partie là où elle en était, seuls les acteurs sont replacés.
        """

        self.paxman.position = tuple(self.paxman.reglage("position-initiale"))
        self.paxman.direction = (0, 0)
        self.paxman.vitesse = self.paxman.reglage("vitesse-défaut")
        self.paxman.facteur = 1.0
        self.fenetre.dessiner_paxman(self.paxman)

        for fantome in self.fantomes.values():
            fantome.position = tuple(fantome.reglage("position-initiale"))
            fantome.direction = (0, 1)
            fantome.mode = self.mode
            self.fenetre.dessiner_fantome(fantome)

    def ajuster_acceleration(self, delta_t: float) -> None:
        """Rapproche le facteur de vitesse de Paxman de sa cible (phase 1)."""
        peut_accelerer = self.paxman.mettre_a_jour_la_jauge(
            self.accelerateur, delta_t
        )
        cible = (
            self.paxman.reglage("accélération-max") if peut_accelerer else 1.0
        )

        if self.paxman.facteur < cible:
            pas = self.paxman.reglage("accélération-montée") * delta_t
            self.paxman.facteur = min(self.paxman.facteur + pas, cible)
        else:
            pas = self.paxman.reglage("accélération-descente") * delta_t
            self.paxman.facteur = max(self.paxman.facteur - pas, cible)

    def alterner_dispersion_poursuite(self, _delta_t: float) -> None:
        """Alterne entre le mode de jeu entre dispersion et poursuite."""

        if self.mode is None or self.mode == "poursuite":
            # mémoriser le mode actuel
            self.mode = "dispersion"

            # passer tous les fantômes en mode dispersion
            for fantome in self.fantomes.values():
                fantome.mode = "dispersion"

            # programmer le prochain changement de mode
            self.fenetre.programmer_appel_fonction(
                self.alterner_dispersion_poursuite,
                self._reglages["dispersion-durée"],
            )

        else:
            # mémoriser le mode actuel
            self.mode = "poursuite"

            # passer tous les fantômes en mode poursuite
            for fantome in self.fantomes.values():
                fantome.mode = "poursuite"

            # programmer le prochain changement de mode
            self.fenetre.programmer_appel_fonction(
                self.alterner_dispersion_poursuite,
                self._reglages["poursuite-durée"],
            )

    def terminer_effet_pilule_force(self, _delta_t: float) -> None:
        """Termine l'effet temporaire de la pilule force."""

        self.paxman.vitesse = self.paxman.reglage("vitesse-défaut")

        for fantome in self.fantomes.values():
            if fantome.mode != "revenant":
                # retourner le fantôme dans le mode actuel du jeu
                fantome.mode = self.mode

        self.fenetre.annuler_appel_fonction(self.alterner_dispersion_poursuite)
        self.fenetre.programmer_appel_fonction(
            self.alterner_dispersion_poursuite,
            self._reglages[f"{self.mode}-durée"],
        )

        # rendre la main à la sirène d'arrière-plan
        self._sons["fantômes-enfuite"].arreter()
        self._sons["sirène"].jouer()

    def signaler_fin_vulnerabilite(self, _delta_t: float) -> None:
        """Avertit que la vulnérabilité des fantômes va bientôt se terminer."""

        for fantome in self.fantomes.values():
            # activer la mutation du fantôme en fuite
            fantome.mutation = fantome.mode == "fuite"

    def ouvrir_les_portes(self, _delta_t: float) -> None:
        """Ouvre toutes les portes."""

        # boucler sur tous les objets du tableau
        for obj in self.plateau.obstacles:
            if isinstance(obj, Porte):
                obj.ouverture = True

        # redessiner les obstacles du plateau
        self.fenetre.dessiner_obstacles(self.plateau)

    def en_cage(self, pos: tuple[float, float]) -> bool:
        """Détermine si la position reçue est à l'intérieur de la cage."""

        # obtenir les coordonnées de la position
        x, y = pos

        # obtenir les coordonnées de la cage
        (x1, y1), (x2, y2) = self.reglage("emplacement-cage")

        # retourner si oui ou non l'acteur est en cage
        return x1 <= x <= x2 and y1 <= y <= y2

    def demarrer_boucle_evenements(self) -> None:
        """Démarre la boucle événementielle du jeu."""

        pyglet.app.run()

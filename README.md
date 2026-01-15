🚀 Fonctionnalités

Authentification complète : Inscription, Connexion, Déconnexion.

Gestion des sujets : Création de discussions, affichage des derniers messages.

Réponses : Ajout de réponses aux sujets existants.

Modération : Suppression de ses propres messages (supprime le sujet si c'est le dernier message).

Design : Interface responsive utilisant Tailwind CSS via CDN.

Sécurité : Hachage des mots de passe, protection CSRF, protection contre les injections SQL (via ORM).

🛠️ Installation

Cloner le dépôt :

git clone https://github.com/T209995/Simple-Python-Forum.git
cd simple-python-forum

Créer un environnement virtuel :

python -m venv venv

# Sur Windows :
venv\Scripts\activate

# Sur macOS/Linux :
source venv/bin/activate

Installer les dépendances :

pip install -r requirements.txt

▶️ Démarrage

Lancez l'application avec la commande suivante :

app.py 

Ouvrez votre navigateur sur http://127.0.0.1:5000.

⚖️ Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, de le modifier et de le distribuer. Voir le fichier LICENSE pour plus de détails.

# UniBooks

Une application Django pour la gestion d'une bibliothèque universitaire.

Caractéristiques principales
- Interface Étudiant (connexion par matricule/email)
- Interface Admin/Bibliothèque (gestion des comptes, livres, demandes)
- Emprunts soumis à validation admin
- Réservations, likes, commentaires
- Notifications et logs d'actions


```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
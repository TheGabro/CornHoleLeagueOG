# CornHole League

Web app per gestire il campionato annuale di cornhole dell'associazione: partite di scontro diretto
(singolo e doppio), conferma del risultato da parte dei partecipanti, classifiche per torneo e combinata.

Stack: Django 6 + Django REST Framework · React (Vite) · PostgreSQL su Neon · login Google (django-allauth).

Il piano di progetto e la roadmap sono in [docs/plan.md](docs/plan.md).

## Setup locale

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # poi compila SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

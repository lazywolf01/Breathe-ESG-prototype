# Breathe ESG Tech Intern Assignment

Focused Django REST + React prototype for ingesting SAP fuel/procurement, utility electricity, and corporate travel data into a normalized analyst review workflow.

## Local setup

```powershell
py -m venv .venv
.\\.venv\\Scripts\\pip install -r requirements.txt
.\\.venv\\Scripts\\python backend\\manage.py migrate
.\\.venv\\Scripts\\python backend\\manage.py runserver
npm install
npm run dev
```

Open the Vite URL, then click **Seed realistic data**. The React app proxies `/api` to Django in development.

## Deployment note

The repo includes `Procfile`, `runtime.txt`, and WhiteNoise static serving. For Render/Railway-style deployment:

```bash
npm install && npm run build
pip install -r requirements.txt
cd backend && python manage.py migrate && python manage.py collectstatic --noinput
gunicorn config.wsgi
```

Set `DEBUG=0`, `SECRET_KEY`, and `ALLOWED_HOSTS` in the deployment environment.

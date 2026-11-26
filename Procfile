# Punto de entrada para Elastic Beanstalk (plataforma Python).
# Beanstalk busca por defecto application.py con un objeto "application";
# este proyecto usa app.py con el objeto "app", así que se declara aquí.
web: gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --access-logfile -

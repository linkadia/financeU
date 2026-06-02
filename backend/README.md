# Finanu Backend

Django + Django REST Framework backend for Finanu.

## Desarrollo en red local

1. Copia `.env.example` a `.env`.
2. Cambia `192.168.0.192` por la IPv4 de tu ordenador si ha cambiado.
3. Arranca Django escuchando en la red local:

```bash
python manage.py runserver 0.0.0.0:8001
```

Desde otro dispositivo en la misma Wi-Fi, la API estará en:

```text
http://192.168.0.192:8001/api/
```

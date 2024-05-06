# wom_app

A WSGI application to create visualizations for [political surveys](https://www.bpb.de/themen/wahl-o-mat/) conducted by the [German Federal Agency for Civic Education](https://www.bpb.de/).

## Local Setup

```
pip install -r requirements.txt
uwsgi --http 127.0.0.1:8000 -w wsgi:app
```
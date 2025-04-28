# Synda API

Cette API REST permet d'interagir avec Synda pour configurer et lancer des pipelines de génération de données synthétiques.

## Installation

Les dépendances requises sont ajoutées au `pyproject.toml`, il vous suffit de les installer :

```bash
poetry install
```

## Démarrage du serveur

```bash
# Méthode 1 : Via la commande synda
poetry run synda api

# Méthode 2 : Directement via le serveur
poetry run python -m synda.api.server
```

Options disponibles :
- `--host` : Adresse d'écoute (par défaut 127.0.0.1)
- `--port` : Port d'écoute (par défaut 8000)
- `--reload` : Mode développement avec auto-reload

Exemple :
```bash
poetry run synda api --host 0.0.0.0 --port 8080 --reload
```

## Documentation de l'API

La documentation Swagger est automatiquement générée et accessible à :
- http://127.0.0.1:8000/docs

## Endpoints disponibles

### Surveillance
- `GET /health` - Vérifier l'état de l'API

### Pipelines
- `POST /pipelines/run` - Lancer un pipeline avec une configuration

### Runs
- `GET /runs` - Lister tous les runs
- `GET /runs/{run_id}` - Obtenir le statut ou le résultat d'un run

### Types d'entrées
- `GET /inputs/types` - Lister tous les types d'entrées disponibles
- `GET /inputs/types/{type_name}` - Obtenir les détails d'un type d'entrée

## Exemples d'utilisation

### Lancer un pipeline (avec fetch)

```javascript
// Exemple avec JavaScript
const response = await fetch('http://localhost:8000/pipelines/run', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    config: {
      pipeline: {
        Input: [
          {
            type: "pdf",
            properties: {
              path: "/chemin/vers/fichier.pdf",
              pages: ["1-3", "5"]
            }
          }
        ],
        // Autres configurations du pipeline...
      }
    }
  })
});

const { run_id } = await response.json();
console.log(`Pipeline lancé avec l'ID: ${run_id}`);
```

### Récupérer le résultat

```javascript
const result = await fetch(`http://localhost:8000/runs/${run_id}`);
const data = await result.json();
// Vérifier data.status, data.result ou data.error
```

## Notes pour le développement

- L'API stocke les runs en mémoire, pour un usage en production, il faudrait utiliser une base de données persistante.
- Les permissions d'accès et l'authentification ne sont pas implémentées, à ajouter selon vos besoins. 
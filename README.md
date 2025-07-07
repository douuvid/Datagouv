# Système d'Automatisation des Candidatures d'Alternance

Interface web pour automatiser les candidatures sur alternance.gouv.fr avec surveillance en temps réel.

## 🎯 Fonctionnalités

- **Recherche automatique** d'offres d'alternance sur alternance.gouv.fr
- **Candidatures automatisées** avec remplissage de formulaires
- **Interface web** avec tableau de bord en temps réel
- **Gestion des documents** (CV, lettres de motivation)
- **Captures d'écran** pour surveillance et débogage
- **Statistiques détaillées** des candidatures
- **Historique complet** avec raisons d'échec

## 🚀 Démarrage rapide

1. **Configurer vos informations personnelles** dans l'onglet Configuration
2. **Uploader vos documents** (CV et lettre de motivation)
3. **Définir vos critères de recherche** (mots-clés, localisation)
4. **Ajuster les paramètres** d'automatisation
5. **Lancer l'automatisation** depuis le tableau de bord

## 📁 Structure du projet

```
├── client/                 # Interface React
├── server/                 # Backend Express.js
├── python_scripts/         # Scripts d'automatisation Python
├── attached_assets/        # Scripts Python originaux
├── uploads/               # Documents uploadés
├── debug_screenshots/     # Captures d'écran
└── logs/                  # Logs d'automatisation
```

## 🔧 Technologies

- **Frontend**: React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Express.js, TypeScript, WebSocket
- **Automatisation**: Python, Selenium, BeautifulSoup
- **Base de données**: PostgreSQL (ou mémoire pour développement)

## ⚙️ Paramètres

- **Délai entre candidatures**: 30 secondes par défaut
- **Nombre max de candidatures**: 10 par session
- **Remplissage automatique**: Activé
- **Envoi automatique**: Configurable
- **Captures d'écran**: Pour surveillance

## 📊 Statistiques

Le système affiche en temps réel :
- Nombre total de candidatures
- Candidatures réussies/échouées
- Temps écoulé
- Raisons d'échec détaillées

## 🔍 Surveillance

- **Logs en temps réel** des activités
- **Captures d'écran** automatiques
- **WebSocket** pour mises à jour instantanées
- **Historique persistant** des sessions

## ⚠️ Important

Ce système utilise l'automatisation web pour faciliter les candidatures. Assurez-vous de respecter les conditions d'utilisation du site alternance.gouv.fr et utilisez le système de manière responsable.# tracker-

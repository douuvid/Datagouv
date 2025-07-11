
Information plus qu'importante n'oublie pas d'integerer le cv , si tu l'oublie tout l code foire 
ca parait fou mais c'est vrai n'oublie pas le cv 


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

## 🤖 Workflow d'automatisation Selenium

Le script Python d'automatisation réalise les étapes suivantes pour chaque candidature :

1. **Chargement du formulaire** :
   - Attente explicite que le formulaire de candidature soit visible et prêt.
2. **Capture d’écran** :
   - Prise d’un screenshot du formulaire avant tout remplissage pour le debug.
3. **Remplissage automatique des champs** :
   - Nom, prénom, email, téléphone, message personnalisé.
   - Effacement robuste de chaque champ avant remplissage (clear, Ctrl+A+Delete, JS).
   - Plusieurs sélecteurs (CSS/XPath) sont essayés pour chaque champ.
   - Mise en évidence visuelle des champs pour le debug.
4. **Gestion des documents (CV et lettre de motivation)** :
   - Recherche des champs d’upload.
   - Vérification si le document est déjà associé au profil utilisateur.
   - Upload manuel du CV si besoin, puis pause de 4 secondes pour laisser le temps au site de traiter le fichier.
   - Capture d’écran après upload.
5. **Cases à cocher (consentement, RGPD, etc.)** :
   - Recherche et activation de toutes les cases à cocher du formulaire.
   - Plusieurs méthodes de clic (label parent, JS direct).
   - Pause de 0,5s entre chaque clic.
6. **Recherche du bouton de soumission** :
   - Recherche du bouton "J’envoie ma candidature" via plusieurs sélecteurs (CSS, XPath, JavaScript).
   - Mise en évidence du bouton et scroll jusqu’à lui.
   - Capture d’écran avant le clic.
7. **Diagnostic des boutons du modal** :
   - Log de tous les boutons présents dans le modal pour debug avant le clic final.
8. **Clic sur le bouton final** :
   - Le script clique sur le bouton final "J’envoie ma candidature" seulement après toutes les étapes précédentes.

### Robustesse et debug
- **Logs détaillés** à chaque étape (succès, échec, valeurs des champs, etc.).
- **Captures d’écran** à chaque étape clé (avant/après remplissage, après upload, avant soumission).
- **Pauses intelligentes** pour laisser le temps au site de traiter les fichiers ou afficher les confirmations.
- **Fallbacks** sur plusieurs sélecteurs et méthodes pour chaque action critique.

Ce workflow garantit que la candidature est envoyée de façon fiable, même si la structure du site évolue légèrement ou si le chargement est lent.

## 🛠️ Configuration étape par étape

1. **Renseigner vos informations personnelles**
   - Ouvrez l'interface web ou modifiez le fichier de configuration utilisateur (selon votre mode d'utilisation).
   - Indiquez : nom, prénom, email, téléphone, message personnalisé.

2. **Uploader vos documents**
   - Ajoutez votre CV (ex : `fake_cv.pdf`) et, si besoin, votre lettre de motivation dans le dossier `uploads/` ou via l'interface.
   - Vérifiez que les fichiers sont bien détectés par le script (voir logs).

3. **Définir vos critères de recherche**
   - Saisissez les mots-clés, localisation, et autres filtres dans l'interface ou le fichier de configuration.

4. **Ajuster les paramètres d'automatisation**
   - Modifiez les variables dans le script ou l'interface :
     - `AUTO_REMPLIR_FORMULAIRE` : active/désactive le remplissage automatique
     - `AUTO_ENVOYER_CANDIDATURE` : active/désactive l'envoi automatique
     - `PAUSE_AVANT_ENVOI` : ajoute une pause avant l'envoi final pour inspection manuelle
     - Délai entre candidatures, nombre max de candidatures, etc.

5. **Lancer l'automatisation**
   - Depuis l'interface web : cliquez sur "Lancer l'automatisation" dans le tableau de bord.
   - En ligne de commande :
     ```bash
     python3 attached_assets/postuler_functions_1751543385370.py
     ```
   - Surveillez les logs et captures d'écran dans les dossiers `logs/` et `debug_screenshots/`.

6. **Analyse des résultats**
   - Consultez le tableau de bord ou les logs pour voir le nombre de candidatures envoyées, les succès/échecs, et les raisons détaillées.

## ⚠️ Important

Ce système utilise l'automatisation web pour faciliter les candidatures. Assurez-vous de respecter les conditions d'utilisation du site alternance.gouv.fr et utilisez le système de manière responsable.# tracker-



Information
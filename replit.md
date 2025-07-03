# replit.md

## Overview

This is a full-stack automation application for alternance (internship) job applications. The system consists of a React frontend dashboard and Express.js backend that interfaces with Python automation scripts to automatically apply to job postings on French job boards.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **UI Library**: Radix UI components with shadcn/ui styling
- **Styling**: Tailwind CSS with custom design tokens
- **State Management**: TanStack Query for server state management
- **Routing**: Wouter for client-side routing
- **Real-time Updates**: WebSocket connection for live status updates

### Backend Architecture
- **Framework**: Express.js with TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **Real-time Communication**: WebSocket Server for broadcasting updates
- **File Management**: Multer for handling CV and cover letter uploads
- **Python Integration**: Child process spawning to run automation scripts

### Database Schema
- **User Configurations**: Personal info, contact details, default messages
- **Automation Sessions**: Track running automation instances with statistics
- **Applications**: Log of job applications with status and metadata
- **Automation Logs**: Detailed logging of automation activities
- **Screenshots**: Debug screenshots for monitoring automation
- **Automation Settings**: Configuration for automation behavior

## Key Components

### Python Automation Scripts
- **Main Script**: `alternance_gouv_1751543361694.py` - Core automation logic
- **Application Functions**: `postuler_functions_1751543385370.py` - Form filling and submission
- **Capture Functions**: `capture_functions_1751543392689.py` - Screenshot and debugging utilities

### Frontend Components
- **Dashboard**: Main interface showing automation status and controls
- **Control Panel**: Start/stop automation with real-time statistics
- **User Configuration**: Form for personal information and application templates
- **Document Management**: CV and cover letter upload interface
- **Activity Feed**: Live log of automation activities
- **Application History**: Table of all job applications with status
- **Screenshot Gallery**: Debug screenshots from automation

### Backend Services
- **Automation Service**: Manages Python script execution and process lifecycle
- **File Service**: Handles document uploads and log exports
- **Storage Service**: Database operations abstraction layer

## Data Flow

1. **User Setup**: User configures personal information and uploads documents
2. **Automation Start**: Backend spawns Python process with user configuration
3. **Job Discovery**: Python scripts scrape job boards for relevant positions
4. **Application Process**: Automated form filling and submission
5. **Real-time Updates**: WebSocket broadcasts progress to frontend
6. **Logging**: All activities logged to database and files
7. **Screenshot Capture**: Debug screenshots saved for monitoring

## External Dependencies

### Frontend Dependencies
- React ecosystem (React, React DOM, React Router)
- TanStack Query for data fetching
- Radix UI component primitives
- Tailwind CSS for styling
- Date-fns for date manipulation
- Lucide React for icons

### Backend Dependencies
- Express.js web framework
- Drizzle ORM with PostgreSQL
- WebSocket (ws) for real-time communication
- Multer for file uploads
- Child process management for Python integration

### Python Dependencies
- Selenium WebDriver for browser automation
- Browser automation libraries
- HTTP request libraries
- File system operations

## Deployment Strategy

### Development Environment
- Vite dev server for frontend hot reloading
- TSX for TypeScript execution in development
- Replit-specific plugins for development environment

### Production Build
- Vite build for optimized frontend bundle
- ESBuild for backend TypeScript compilation
- Static file serving from Express

### Database Management
- Drizzle Kit for schema migrations
- PostgreSQL connection via environment variables
- Neon Database serverless PostgreSQL

## Changelog

- July 03, 2025: Configuration réelle sans simulation
  - Suppression complète des données simulées
  - Integration des vrais scripts Python d'automatisation
  - Configuration Python 3.11 avec Selenium et dépendances
  - Création du script automation_runner.py pour interface web
  - Structure de dossiers organisée et .gitignore mis à jour
  - Système prêt pour vraies candidatures sur alternance.gouv.fr
  
- July 03, 2025: Amélioration de l'interface et gestion d'erreurs
  - Ajout d'analyses détaillées des échecs de candidature
  - 5 raisons d'échec réalistes avec pourcentages
  - Correction WebSocket pour mises à jour temps réel
  - Affichage des erreurs dans l'historique des candidatures
  - Boutons d'action pour captures d'écran et téléchargement de rapports

- July 03, 2025: Niveaux de formation et simplification interface
  - Ajout des niveaux de formation exacts d'alternance.gouv.fr
  - Configuration du rayon de recherche (10km à toute la France)
  - Suppression du champ "Type d'emploi" - focus uniquement alternance
  - Correction des erreurs React et interface fonctionnelle
  - Scripts Python mis à jour avec nouveaux paramètres

- July 03, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.
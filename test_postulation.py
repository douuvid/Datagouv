#!/usr/bin/env python3
"""
Script de test pour la postulation automatique
"""

import json
import sys
import os

# Données de test
test_config = {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john.doe@example.com",
    "phone": "+33123456789",
    "message": "Je suis passionné par le développement web et je recherche une alternance pour approfondir mes compétences.",
    "cvPath": "uploads/cv.pdf",
    "coverLetterPath": "uploads/cover_letter.pdf",
    "searchKeywords": "marketing, communication, digital",
    "location": "Paris",
    "jobTypes": "alternance, stage",
    "contractTypes": "CDI, CDD, alternance",
    "educationLevel": "licence",
    "searchRadius": "50",
    "search_query": "marketing",
    "settings": {
        "delayBetweenApplications": 5,
        "maxApplicationsPerSession": 3,
        "autoFillForm": True,
        "autoSendApplication": True,
        "pauseBeforeSend": False,
        "captureScreenshots": True
    }
}

if __name__ == "__main__":
    print("🚀 Test de postulation automatique")
    print("Configuration:", json.dumps(test_config, indent=2))
    
    # Lancer le script d'automatisation
    import subprocess
    
    try:
        # Créer les dossiers nécessaires
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("debug_screenshots", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Créer des fichiers de test si ils n'existent pas
        if not os.path.exists("uploads/cv.pdf"):
            with open("uploads/cv.pdf", "w") as f:
                f.write("CV de test")
        
        if not os.path.exists("uploads/cover_letter.pdf"):
            with open("uploads/cover_letter.pdf", "w") as f:
                f.write("Lettre de motivation de test")
        
        print("📁 Dossiers et fichiers de test créés")
        
        # Lancer le script d'automatisation
        print("🤖 Lancement de l'automatisation...")
        
        # Passer la configuration via stdin
        process = subprocess.Popen(
            ["python3", "python_scripts/automation_runner.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=json.dumps(test_config))
        
        print("📤 Sortie du script:")
        print(stdout)
        
        if stderr:
            print("❌ Erreurs:")
            print(stderr)
            
    except Exception as e:
        print(f"❌ Erreur: {e}") 
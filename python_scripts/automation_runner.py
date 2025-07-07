#!/usr/bin/env python3
"""
Automation Runner - Interface between the web application and the existing Python automation scripts
"""

import json
import sys
import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
import time

# Add the attached_assets directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'attached_assets'))

# Import the main automation script
try:
    from alternance_gouv_1751543361694 import run_scraper, setup_driver, parse_results
    from postuler_functions_1751543385370 import postuler_offre, remplir_formulaire_candidature
    from capture_functions_1751543392689 import capture_and_highlight, switch_to_iframe_if_needed
    SCRIPTS_LOADED = True
except ImportError as e:
    logging.error(f"Failed to import automation scripts: {e}")
    SCRIPTS_LOADED = False

class AutomationRunner:
    def __init__(self, session_id: int, user_config: Dict[str, Any], settings: Dict[str, Any]):
        self.session_id = session_id
        self.user_config = user_config
        self.settings = settings
        self.driver = None
        self.applications_processed = 0
        self.successful_applications = 0
        self.failed_applications = 0
        
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/automation_{self.session_id}.log'),
                logging.StreamHandler()
            ]
        )
        
    def log_message(self, level: str, message: str, metadata: Optional[Dict] = None):
        """Log a message that will be sent to the web interface"""
        log_entry = {
            'type': 'log',
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'metadata': metadata or {}
        }
        
        # Send to web interface via stdout
        print(f"WEB_LOG: {json.dumps(log_entry)}")
        
        # Also log locally
        getattr(logging, level.lower(), logging.info)(message)
    
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to the web interface"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        print(f"WEB_EVENT: {json.dumps(event)}")
    
    def setup_driver(self):
        """Setup the Selenium WebDriver"""
        try:
            self.log_message('info', 'Configuration du navigateur Chrome...')
            self.driver = setup_driver()
            self.log_message('success', 'Navigateur configuré avec succès')
            return True
        except Exception as e:
            self.log_message('error', f'Erreur lors de la configuration du navigateur: {str(e)}')
            return False
    
    def capture_screenshot(self, description: str, application_data: Optional[Dict] = None):
        """Capture a screenshot and notify the web interface"""
        try:
            if not self.driver:
                return None
                
            filename = f"debug_screenshots/session_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            if SCRIPTS_LOADED:
                capture_and_highlight(self.driver, None, description)
            else:
                self.driver.save_screenshot(filename)
            
            # Notify web interface
            screenshot_data = {
                'session_id': self.session_id,
                'file_path': filename,
                'description': description,
                'captured_at': datetime.now().isoformat()
            }
            
            if application_data:
                screenshot_data['application_id'] = application_data.get('id')
            
            self.emit_event('screenshot_captured', screenshot_data)
            return filename
            
        except Exception as e:
            self.log_message('error', f'Erreur lors de la capture: {str(e)}')
            return None
    
    def process_application(self, offer_data: Dict[str, Any]) -> bool:
        """Process a single job application"""
        try:
            self.log_message('info', f'Traitement de l\'offre: {offer_data["title"]}')
            
            # Create application record
            application_data = {
                'session_id': self.session_id,
                'job_title': offer_data['title'],
                'company': offer_data.get('company', 'Non spécifié'),
                'location': offer_data.get('location', 'Non spécifié'),
                'status': 'pending',
                'applied_at': datetime.now().isoformat()
            }
            
            self.emit_event('application_started', application_data)
            
            # Capture screenshot before processing
            self.capture_screenshot(f"Avant candidature - {offer_data['title']}", application_data)
            
            # Process the application
            success = self.fill_application_form(offer_data, application_data)
            
            if success:
                application_data['status'] = 'completed'
                self.successful_applications += 1
                self.log_message('success', f'Candidature envoyée avec succès pour {offer_data["title"]}')
            else:
                application_data['status'] = 'failed'
                application_data['error_message'] = 'Échec lors du remplissage du formulaire'
                self.failed_applications += 1
                self.log_message('error', f'Échec de candidature pour {offer_data["title"]}')
            
            # Capture screenshot after processing
            self.capture_screenshot(f"Après candidature - {offer_data['title']}", application_data)
            
            self.emit_event('application_completed', application_data)
            self.applications_processed += 1
            
            return success
            
        except Exception as e:
            self.log_message('error', f'Erreur lors du traitement de l\'offre: {str(e)}')
            traceback.print_exc()
            return False
    
    def fill_application_form(self, offer_data: Dict[str, Any], application_data: Dict[str, Any]) -> bool:
        """Fill the application form using the existing automation functions"""
        try:
            if not SCRIPTS_LOADED:
                self.log_message('warning', 'Scripts d\'automatisation non chargés, simulation de candidature')
                return True
            
            # Use the existing postuler_offre function
            url_offre = offer_data.get('url', '')
            titre_offre = offer_data.get('title', '')
            
            if not url_offre:
                self.log_message('error', 'URL de l\'offre manquante')
                return False
            
            # Navigate to the offer and apply
            success = postuler_offre(self.driver, url_offre, titre_offre, self.user_config)
            
            return success
            
        except Exception as e:
            self.log_message('error', f'Erreur lors du remplissage du formulaire: {str(e)}')
            return False
    
    def update_session_stats(self):
        """Update and emit session statistics"""
        stats = {
            'total_applications': self.applications_processed,
            'successful_applications': self.successful_applications,
            'failed_applications': self.failed_applications,
            'session_id': self.session_id
        }
        
        self.emit_event('session_stats_updated', stats)
    
    def run(self):
        """Main automation loop"""
        try:
            self.log_message('info', 'Démarrage de l\'automatisation réelle...')
            
            if not SCRIPTS_LOADED:
                self.log_message('error', 'Scripts d\'automatisation non disponibles')
                return
            
            # Setup WebDriver
            if not self.setup_driver():
                self.log_message('error', 'Impossible de configurer le navigateur')
                return
            
            # Extract search parameters from user config
            search_params = {
                'keywords': self.user_config.get('searchKeywords', ''),
                'location': self.user_config.get('searchLocation', ''),
                'contract_types': self.user_config.get('contractTypes', []),
                'education_level': self.user_config.get('educationLevel', ''),
                'search_radius': self.user_config.get('searchRadius', '30')
            }
            
            self.log_message('info', f'Recherche avec les critères: {search_params}')
            
            # Run the scraper to get job offers
            offers = run_scraper(self.user_config)
            
            if not offers:
                self.log_message('warning', 'Aucune offre trouvée avec les critères spécifiés')
                return
            
            self.log_message('success', f'{len(offers)} offres trouvées')
            
            # Process each offer
            max_applications = self.settings.get('maxApplicationsPerSession', 10)
            delay_between_applications = self.settings.get('delayBetweenApplications', 30)
            
            for i, offer in enumerate(offers[:max_applications]):
                self.log_message('info', f'Traitement de l\'offre {i+1}/{min(len(offers), max_applications)}')
                
                # Process the application
                self.process_application(offer)
                
                # Update statistics
                self.update_session_stats()
                
                # Wait between applications
                if i < len(offers) - 1:
                    self.log_message('info', f'Attente de {delay_between_applications} secondes avant la prochaine candidature')
                    import time
                    time.sleep(delay_between_applications)
            
            self.log_message('success', 'Automatisation terminée avec succès')
            
        except Exception as e:
            self.log_message('error', f'Erreur fatale: {str(e)}')
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
            
            # Final statistics
            self.update_session_stats()
            self.emit_event('session_completed', {
                'session_id': self.session_id,
                'total_applications': self.applications_processed,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            })

def main():
    """Main entry point"""
    try:
        # Read configuration from stdin
        input_data = sys.stdin.read()
        config = json.loads(input_data)
        
        session_id = int(os.environ.get('AUTOMATION_SESSION_ID', '1'))
        user_config = config
        settings = config.get('settings', {})
        
        # Create and run automation
        runner = AutomationRunner(session_id, user_config, settings)
        runner.run()
        
    except Exception as e:
        error_msg = f"Erreur fatale dans le runner: {str(e)}"
        print(f"WEB_LOG: {json.dumps({'type': 'log', 'level': 'error', 'message': error_msg})}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
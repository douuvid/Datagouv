#!/usr/bin/env python3
"""
Automation Runner - Interface between the web application and the existing Python automation scripts
"""

import os
import sys
import json
import argparse
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Add the parent directory to the path to import the existing scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from attached_assets.alternance_gouv_1751543361694 import (
        setup_driver, 
        search_offers, 
        process_offers,
        logger as base_logger
    )
    from attached_assets.postuler_functions_1751543385370 import (
        remplir_formulaire_candidature,
        postuler_offre
    )
    from attached_assets.capture_functions_1751543392689 import (
        capture_and_highlight,
        switch_to_iframe_if_needed
    )
except ImportError as e:
    print(f"JSON:{json.dumps({'type': 'log', 'data': {'level': 'error', 'message': f'Failed to import automation modules: {e}'}})}")
    sys.exit(1)

class AutomationRunner:
    def __init__(self, session_id: int, user_config: Dict[str, Any], settings: Dict[str, Any]):
        self.session_id = session_id
        self.user_config = user_config
        self.settings = settings
        self.driver = None
        self.running = False
        self.total_applications = 0
        self.successful_applications = 0
        self.failed_applications = 0
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(f'automation_runner_{self.session_id}')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler that outputs JSON for the web interface
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
    def log_message(self, level: str, message: str, metadata: Optional[Dict] = None):
        """Log a message that will be sent to the web interface"""
        log_data = {
            'type': 'log',
            'data': {
                'level': level,
                'message': message,
                'metadata': metadata or {}
            }
        }
        print(f"JSON:{json.dumps(log_data)}")
        
    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to the web interface"""
        event_data = {
            'type': event_type,
            'data': data
        }
        print(f"JSON:{json.dumps(event_data)}")
        
    def setup_driver(self):
        """Setup the Selenium WebDriver"""
        try:
            self.log_message('info', 'Setting up browser driver...')
            self.driver = setup_driver(headless=not self.settings.get('showBrowser', False))
            self.log_message('success', 'Browser driver setup completed')
            return True
        except Exception as e:
            self.log_message('error', f'Failed to setup browser driver: {str(e)}')
            return False
            
    def capture_screenshot(self, description: str, application_data: Optional[Dict] = None):
        """Capture a screenshot and notify the web interface"""
        try:
            if not self.settings.get('captureScreenshots', True):
                return
                
            timestamp = int(time.time())
            filename = f"automation_session_{self.session_id}_{timestamp}_{description.replace(' ', '_')}.png"
            filepath = os.path.join('debug_screenshots', filename)
            
            self.driver.save_screenshot(filepath)
            
            screenshot_data = {
                'filePath': filepath,
                'description': description,
                'applicationId': application_data.get('id') if application_data else None
            }
            
            self.emit_event('screenshot_captured', screenshot_data)
            self.log_message('info', f'Screenshot captured: {description}')
            
        except Exception as e:
            self.log_message('error', f'Failed to capture screenshot: {str(e)}')
            
    def process_application(self, offer_data: Dict[str, Any]) -> bool:
        """Process a single job application"""
        try:
            # Notify web interface that application started
            application_data = {
                'jobTitle': offer_data.get('title', 'Unknown'),
                'company': offer_data.get('company', 'Unknown'),
                'location': offer_data.get('location', 'Unknown')
            }
            
            self.emit_event('application_started', application_data)
            self.log_message('info', f"Starting application for: {application_data['jobTitle']}")
            
            # Capture screenshot before starting
            self.capture_screenshot(f"starting_application_{application_data['jobTitle']}", application_data)
            
            # Fill and submit the application form
            success = self.fill_application_form(offer_data, application_data)
            
            if success:
                self.successful_applications += 1
                application_data['status'] = 'sent'
                self.log_message('success', f"Application sent successfully for: {application_data['jobTitle']}")
            else:
                self.failed_applications += 1
                application_data['status'] = 'failed'
                application_data['errorMessage'] = 'Failed to submit application'
                self.log_message('error', f"Application failed for: {application_data['jobTitle']}")
            
            # Capture screenshot after completion
            self.capture_screenshot(f"completed_application_{application_data['jobTitle']}", application_data)
            
            # Notify web interface of completion
            self.emit_event('application_completed', application_data)
            
            # Update session statistics
            self.update_session_stats()
            
            return success
            
        except Exception as e:
            self.log_message('error', f'Error processing application: {str(e)}')
            return False
            
    def fill_application_form(self, offer_data: Dict[str, Any], application_data: Dict[str, Any]) -> bool:
        """Fill the application form using the existing automation functions"""
        try:
            # Use the existing form filling logic
            return remplir_formulaire_candidature(
                self.driver,
                self.user_config,
                offer_data.get('title', 'Unknown')
            )
        except Exception as e:
            self.log_message('error', f'Error filling application form: {str(e)}')
            return False
            
    def update_session_stats(self):
        """Update and emit session statistics"""
        self.total_applications = self.successful_applications + self.failed_applications
        
        stats_data = {
            'totalApplications': self.total_applications,
            'successfulApplications': self.successful_applications,
            'failedApplications': self.failed_applications
        }
        
        self.emit_event('session_stats', stats_data)
        
    def run(self):
        """Main automation loop"""
        try:
            self.log_message('info', f'Starting automation session {self.session_id}')
            self.running = True
            
            # Setup browser driver
            if not self.setup_driver():
                return False
                
            # Navigate to the job search site
            self.log_message('info', 'Navigating to job search site...')
            self.driver.get('https://www.alternance.gouv.fr/')
            
            # Wait for page to load
            time.sleep(3)
            self.capture_screenshot('homepage_loaded')
            
            # Search for offers (this would use the existing search logic)
            self.log_message('info', 'Searching for job offers...')
            
            # Mock offers for demonstration (replace with actual search logic)
            offers = [
                {
                    'title': 'Développeur Full Stack - Alternance',
                    'company': 'TechCorp SAS',
                    'location': 'Paris, France'
                },
                {
                    'title': 'Développeur React - Stage',
                    'company': 'InnovateLab',
                    'location': 'Lyon, France'
                }
            ]
            
            self.log_message('info', f'Found {len(offers)} job offers')
            
            # Process each offer
            for i, offer in enumerate(offers):
                if not self.running:
                    break
                    
                self.log_message('info', f'Processing offer {i+1}/{len(offers)}: {offer["title"]}')
                
                # Process the application
                self.process_application(offer)
                
                # Check if we've reached the maximum applications
                if self.total_applications >= self.settings.get('maxApplicationsPerSession', 50):
                    self.log_message('info', 'Maximum applications per session reached')
                    break
                    
                # Wait between applications
                delay = self.settings.get('delayBetweenApplications', 30)
                if delay > 0 and i < len(offers) - 1:
                    self.log_message('info', f'Waiting {delay} seconds before next application...')
                    time.sleep(delay)
                    
            self.log_message('info', f'Automation session completed. Total: {self.total_applications}, Success: {self.successful_applications}, Failed: {self.failed_applications}')
            
        except KeyboardInterrupt:
            self.log_message('info', 'Automation stopped by user')
        except Exception as e:
            self.log_message('error', f'Automation error: {str(e)}')
        finally:
            if self.driver:
                self.driver.quit()
                self.log_message('info', 'Browser driver closed')
            
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Automation Runner')
    parser.add_argument('--session-id', type=int, required=True, help='Session ID')
    parser.add_argument('--user-config', type=str, required=True, help='User configuration JSON')
    parser.add_argument('--settings', type=str, required=True, help='Automation settings JSON')
    
    args = parser.parse_args()
    
    try:
        user_config = json.loads(args.user_config)
        settings = json.loads(args.settings)
    except json.JSONDecodeError as e:
        print(f"JSON:{json.dumps({'type': 'log', 'data': {'level': 'error', 'message': f'Invalid JSON configuration: {e}'}})}")
        sys.exit(1)
    
    # Create and run the automation
    runner = AutomationRunner(args.session_id, user_config, settings)
    success = runner.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

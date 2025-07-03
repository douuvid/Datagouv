import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def capture_and_highlight(driver, element, description=""):
    """
    Capture une capture d'écran en surlignant un élément spécifique
    """
    try:
        # Créer le répertoire des captures d'écran s'il n'existe pas
        if not os.path.exists('debug_screenshots'):
            os.makedirs('debug_screenshots')
            
        # Sauvegarder le style original de l'élément
        original_style = driver.execute_script("return arguments[0].getAttribute('style');", element)
        
        # Appliquer une bordure rouge et un surlignage pour mettre en évidence l'élément
        driver.execute_script("""
            arguments[0].setAttribute('style', 
            'border: 3px solid red; background-color: yellow; padding: 3px;');
        """, element)
        
        # Générer un nom de fichier basé sur la description et un timestamp
        safe_description = description.replace(' ', '_').replace('/', '_').lower()
        timestamp = int(time.time())
        filename = f"debug_screenshots/highlight_{safe_description}_{timestamp}.png"
        
        # Prendre la capture d'écran
        driver.save_screenshot(filename)
        logger.info(f"Capture d'écran avec élément surligné: {filename}")
        
        # Restaurer le style original
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, original_style)
        
        return filename
    except Exception as e:
        logger.error(f"Erreur lors de la capture avec surlignage: {e}")
        return None

def switch_to_iframe_if_needed(driver):
    """
    Bascule vers l'iframe des résultats si nécessaire
    """
    try:
        # Vérifier si on est déjà dans l'iframe
        try:
            # Tenter d'accéder à un élément qui n'existe que dans l'iframe
            driver.find_element(By.CSS_SELECTOR, ".result-card")
            logger.info("Déjà dans l'iframe des résultats")
            return True
        except:
            # On n'est pas dans l'iframe, on tente d'y accéder
            logger.info("Tentative de basculement vers l'iframe des résultats...")
            pass
        
        # Revenir au contexte principal
        driver.switch_to.default_content()
        
        # Essayer de trouver l'iframe et y basculer
        iframe_selectors = [
            "iframe#lba-results-iframe",
            "iframe.lba-results-iframe",
            "iframe[src*='labonnealternance']",
            "iframe"
        ]
        
        for selector in iframe_selectors:
            try:
                wait = WebDriverWait(driver, 5)
                iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                driver.switch_to.frame(iframe)
                logger.info(f"Basculement réussi vers l'iframe avec sélecteur: {selector}")
                return True
            except Exception as e:
                logger.debug(f"Impossible de basculer vers l'iframe avec sélecteur {selector}: {e}")
                continue
        
        # Si aucun iframe n'est trouvé
        logger.warning("Aucun iframe de résultats trouvé")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du basculement vers l'iframe: {e}")
        return False

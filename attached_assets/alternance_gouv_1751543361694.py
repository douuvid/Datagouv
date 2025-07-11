import logging
import os
import time
import sys
import datetime
import random
import re
from urllib.parse import urlparse, unquote, parse_qs
from postuler_functions_1751543385370 import remplir_formulaire_candidature, postuler_offre, AUTO_REMPLIR_FORMULAIRE, AUTO_ENVOYER_CANDIDATURE
from capture_functions_1751543392689 import capture_and_highlight, switch_to_iframe_if_needed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, ElementClickInterceptedException, 
    StaleElementReferenceException, WebDriverException, ElementNotInteractableException
)
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import argparse
import os

# Configuration pour la postulation automatique
AUTO_POSTULER = True  # Activer/désactiver la postulation automatique
PAUSE_APRES_POSTULATION = False  # Mettre en pause après ouverture du formulaire pour inspection manuelle

# Import des fonctions auxiliaires
try:
    POSTULER_FUNCTIONS_LOADED = True
except ImportError:
    print("Module postuler_functions non trouvé, la postulation automatisée ne sera pas disponible")
    POSTULER_FUNCTIONS_LOADED = False

try:
    CAPTURE_FUNCTIONS_LOADED = True
except ImportError:
    print("Module capture_functions non trouvé, les fonctions de capture améliorées ne seront pas disponibles")
    CAPTURE_FUNCTIONS_LOADED = False
    
    # Fonction de remplacement simple si le module n'est pas disponible
    def capture_and_highlight(driver, element, description=""):
        try:
            if not os.path.exists('debug_screenshots'):
                os.makedirs('debug_screenshots')
            filename = f"debug_screenshots/{description.replace(' ', '_')}.png"
            driver.save_screenshot(filename)
            return filename
        except Exception as e:
            print(f"Erreur lors de la capture: {e}")
            return None
            
    def switch_to_iframe_if_needed(driver):
        try:
            driver.switch_to.default_content()
            iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
            driver.switch_to.frame(iframe)
            return True
        except Exception:
            return False

# Ajout du chemin racine du projet pour permettre les imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)


# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Fonctions auxiliaires ---




def switch_to_iframe_if_needed(driver):
    """Bascule vers l'iframe de résultats si nécessaire"""
    try:
        # Vérifier si nous sommes déjà dans l'iframe
        try:
            # Si cet élément est accessible, nous ne sommes pas dans l'iframe
            driver.find_element(By.TAG_NAME, 'iframe')
            is_in_iframe = False
        except:
            # Si l'élément n'est pas trouvé, nous sommes peut-être déjà dans l'iframe
            is_in_iframe = True
        
        if not is_in_iframe:
            # Essayer de trouver l'iframe et y basculer
            iframe_selectors = [
                "iframe#labnframe",
                "iframe#laBonneAlternance", 
                "iframe.labonne",
                "iframe[title*='La Bonne Alternance']", 
                "iframe"
            ]
            
            for selector in iframe_selectors:
                try:
                    iframe = driver.find_element(By.CSS_SELECTOR, selector)
                    if iframe.is_displayed():
                        driver.switch_to.frame(iframe)
                        logger.info(f"Basculé vers l'iframe avec le sélecteur: {selector}")
                        return True
                except Exception as e:
                    continue
            
            logger.warning("Impossible de trouver l'iframe des résultats")
            return False
        else:
            logger.info("Déjà dans l'iframe")
            return True
    except Exception as e:
        logger.error(f"Erreur lors de la tentative de basculer vers l'iframe: {e}")
        return False

# --- Fonctions robustes de bas niveau (inspirées du code utilisateur) ---

def uncheck_formations_checkbox(driver, wait):
    """Décoche la case 'Formations' si elle est cochée avec plusieurs méthodes pour assurer la compatibilité React."""
    try:
        logger.info("Tentative de décocher la case 'Formations'...")
        
        # Capture d'écran avant décochage pour déboguer
        driver.save_screenshot('debug_screenshots/avant_decochage_formations.png')
        
        # Recherche agressive de la case Formations par plusieurs méthodes
        formations_checkbox_found = False
        checkbox = None
        
        # Méthode 1: Cibler directement par attribut name='formations'
        try:
            checkbox_selectors = [
                "input[name='formations'][type='checkbox']",
                "input#formations",
                "input[type='checkbox'][name*='formation']",
                "input[type='checkbox'][id*='formation']",
                "input[name*='formation']",
                "input[aria-label*='formation' i][type='checkbox']",  # 'i' pour insensible à la casse
                "input[type='checkbox']"
            ]
            
            for selector in checkbox_selectors:
                try:
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, selector)
                    if checkboxes:
                        for cb in checkboxes:
                            try:
                                # Vérifier si c'est la case formations en vérifiant les attributs ou le texte autour
                                parent = driver.execute_script("return arguments[0].parentNode;", cb)
                                parent_text = parent.text.lower() if parent else ""
                                
                                if (cb.get_attribute('name') == 'formations' or 
                                    'formation' in (cb.get_attribute('id') or '') or 
                                    'formation' in parent_text):
                                    checkbox = cb
                                    formations_checkbox_found = True
                                    logger.info(f"Case 'Formations' trouvée avec le sélecteur: {selector}")
                                    break
                            except Exception:
                                continue
                        if formations_checkbox_found:
                            break
                except Exception:
                    continue
            
            # Si toujours pas trouvée, essayer par XPath
            if not checkbox:
                xpath_selectors = [
                    "//input[@type='checkbox' and contains(@name, 'formation')]",
                    "//input[@type='checkbox' and contains(@id, 'formation')]",
                    "//label[contains(translate(text(), 'FORMATIONS', 'formations'), 'formation')]/input[@type='checkbox']",
                    "//label[contains(translate(text(), 'FORMATIONS', 'formations'), 'formation')]/following::input[@type='checkbox'][1]",
                    "//input[@type='checkbox']/following::*[contains(translate(text(), 'FORMATIONS', 'formations'), 'formation')]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        if elements:
                            checkbox = elements[0]
                            formations_checkbox_found = True
                            logger.info(f"Case 'Formations' trouvée avec le XPath: {xpath}")
                            break
                    except Exception:
                        continue
            
            # Vérification initiale et multiples tentatives de décocher pour React
            if checkbox:
                for attempt in range(3):  # Faire plusieurs tentatives
                    time.sleep(1)  # Pause entre les tentatives
                    
                    # Vérifier si la case est cochée ou si on force le décochage
                    force_uncheck = True  # Toujours forcer le décochage pour s'éviter des problèmes
                    is_checked = checkbox.is_selected() or checkbox.get_attribute('checked') == 'true'
                    
                    if is_checked or force_uncheck:
                        logger.info(f"Case 'Formations' trouvée et {'elle est cochée' if is_checked else 'forçage du décochage'} - tentative {attempt+1}")

                    
                    # Méthode 1: JavaScript complet pour React (la plus efficace)
                    try:
                        # Cette méthode simule tous les événements React nécessaires
                        js_code = """
                        arguments[0].checked = false;
                        arguments[0].setAttribute('checked', false);
                        var event = new Event('change', { 'bubbles': true, 'cancelable': true });
                        arguments[0].dispatchEvent(event);
                        // Pour React, simuler aussi un click en plus du change
                        var clickEvent = new MouseEvent('click', {
                            'bubbles': true,
                            'cancelable': true,
                            'view': window
                        });
                        arguments[0].dispatchEvent(clickEvent);
                        // Forcer la mise à jour de l'interface React
                        if (arguments[0]._valueTracker) {
                            arguments[0]._valueTracker.setValue(false);
                        }
                        """
                        driver.execute_script(js_code, checkbox)
                        time.sleep(0.5)  # Attendre la propagation des événements
                        logger.info("✅ Case 'Formations' décochée via JavaScript complet pour React")
                        
                        # Vérifier si ça a fonctionné après la modification
                        if not checkbox.is_selected() and checkbox.get_attribute('checked') != 'true':
                            logger.info("✓ Vérification: la case est bien décochée")
                            return True
                    except Exception as e:
                        logger.warning(f"Échec du JS complet pour React: {e}")
                    
                    # Méthode 2: Clic direct (si JS a échoué)
                    try:
                        checkbox.click()
                        time.sleep(0.5)
                        if not checkbox.is_selected() and checkbox.get_attribute('checked') != 'true':
                            logger.info("✅ Case 'Formations' décochée via clic direct")
                            return True
                    except Exception as e:
                        logger.warning(f"Échec du clic direct: {e}")
                    
                    # Méthode 3: ActionChains (si les autres ont échoué)
                    try:
                        ActionChains(driver).move_to_element(checkbox).click().perform()
                        time.sleep(0.5)
                        logger.info("✅ Case 'Formations' décochée via ActionChains")
                        
                        # Double vérification après ActionChains
                        if not checkbox.is_selected() and checkbox.get_attribute('checked') != 'true':
                            return True
                    except Exception as e:
                        logger.warning(f"Échec du ActionChains: {e}")
                else:
                    logger.info("La case 'Formations' est déjà décochée")
                    return True
                
        except Exception as e:
            logger.warning(f"Impossible de trouver la case 'Formations' par nom: {e}")
            
        # Tenter de trouver par data-attribute
        try:
            checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-fr-js-checkbox-input='true']")))
            parent_text = driver.execute_script("return arguments[0].parentElement.textContent;", checkbox)
            
            if 'formations' in parent_text.lower() and (checkbox.is_selected() or checkbox.get_attribute('checked') == 'true'):
                # Utiliser JavaScript qui est plus fiable pour les cases à cocher
                driver.execute_script("arguments[0].checked = false;", checkbox)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', { 'bubbles': true }));", checkbox)
                logger.info("✅ Case 'Formations' décochée avec succès via data-attribute")
                return True
        except Exception as e:
            logger.warning(f"Impossible de trouver la case par data-attribute: {e}")
            
        # Cibler par texte du label adjacent
        try:
            # Trouver tous les labels qui contiennent 'Formations'
            formations_labels = driver.find_elements(By.XPATH, "//label[contains(text(), 'Formations')]")
            
            for label in formations_labels:
                # Trouver le checkbox associé par son ID
                label_for = label.get_attribute('for')
                if label_for:
                    try:
                        checkbox = driver.find_element(By.ID, label_for)
                        if checkbox.is_selected() or checkbox.get_attribute('checked') == 'true':
                            driver.execute_script("arguments[0].checked = false;", checkbox)
                            logger.info("✅ Case 'Formations' décochée avec succès via label")
                            return True
                    except Exception as inner_e:
                        continue
        except Exception as e:
            logger.warning(f"Impossible de trouver la case par texte du label: {e}")
        
        # Essayer chaque sélecteur jusqu'à trouver le checkbox
        checkbox = None
        for selector in checkbox_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                # Filtrer pour ne garder que les éléments visibles et cochés
                visible_checkboxes = [el for el in elements if el.is_displayed() and el.get_attribute('checked') == 'true']
                if visible_checkboxes:
                    checkbox = visible_checkboxes[0]
                    logger.info(f"Case 'Formations' trouvée avec le sélecteur: {selector}")
                    break
            except Exception as e:
                continue
        
        # Si on n'a pas trouvé avec CSS, essayer avec XPath pour le texte du label
        if not checkbox:
            try:
                # XPath pour trouver un checkbox avec un label contenant 'Formations'
                xpath = "//label[contains(text(), 'Formations')]/preceding-sibling::input[@type='checkbox'] | //label[contains(text(), 'Formations')]/../input[@type='checkbox']"
                elements = driver.find_elements(By.XPATH, xpath)
                visible_checkboxes = [el for el in elements if el.is_displayed() and el.get_attribute('checked') == 'true']
                if visible_checkboxes:
                    checkbox = visible_checkboxes[0]
                    logger.info("Case 'Formations' trouvée avec XPath")
            except Exception as e:
                logger.warning(f"Erreur lors de la recherche par XPath: {e}")
        
        # Si on a trouvé le checkbox et qu'il est coché
        if checkbox and checkbox.is_selected():
            try:
                # Essayer de cliquer directement
                checkbox.click()
                logger.info("✅ Case 'Formations' décochée avec succès")
            except Exception as e:
                logger.warning(f"Erreur lors du clic direct: {e}")
                # Essayer avec JavaScript si le clic direct ne fonctionne pas
                try:
                    driver.execute_script("arguments[0].click();", checkbox)
                    logger.info("✅ Case 'Formations' décochée via JavaScript")
                except Exception as e2:
                    logger.warning(f"Échec du clic via JavaScript: {e2}")
                    # Dernière tentative avec Actions
                    try:
                        ActionChains(driver).move_to_element(checkbox).click().perform()
                        logger.info("✅ Case 'Formations' décochée via ActionChains")
                    except Exception as e3:
                        logger.error(f"❌ Impossible de décocher la case 'Formations': {e3}")
        elif checkbox:
            logger.info("La case 'Formations' est déjà décochée")
        else:
            logger.warning("❓ Case 'Formations' non trouvée")
            # Capture d'écran pour analyser le problème
            screenshot_path = "debug_screenshots/checkbox_not_found.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            driver.save_screenshot(screenshot_path)
            logger.info(f"Capture d'écran enregistrée dans {screenshot_path}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la tentative de décocher la case 'Formations': {e}")

def setup_driver():
    """Configure un driver Chrome robuste sans ouverture automatique des DevTools."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Désactiver le mode headless pour permettre les interactions visuelles
    # options.headless = False  # Supprimé car obsolète
    # Pour le mode headless, décommente la ligne suivante :
    # options.add_argument("--headless=new")
    
    # Simuler un user-agent avec DevTools ouverts
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Chrome-Lighthouse")
    
    # RETRAIT de l'option --auto-open-devtools-for-tabs qui cause des problèmes de fenêtre
    
    # Configurer préférences pour outils de développement (sans les ouvrir automatiquement)
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "devtools.preferences": {"currentDockState": "\"bottom\"", "panel-selectedTab": "\"elements\""},
        "devtools.open_docked": True
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(120)  # Timeout plus long
        
        logger.info("Driver Chrome créé avec succès")
        return driver
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du driver: {e}")
        return None

def select_suggestion(driver, wait, timeout=5):
    """Sélectionne la première suggestion dans la liste d'autocomplétion."""
    # Différents sélecteurs possibles pour la liste de suggestions
    suggestion_selectors = [
        # Sélecteurs spécifiques au site alternance.emploi.gouv.fr
        ".suggestions",  # Vérifié sur le site
        ".suggestions-container",
        ".listbox",
        "#ac-metier-item-list",  # ID spécifique pour le champ métier
        "#ac-lieu-item-list",    # ID spécifique pour le champ lieu
        # Sélecteurs génériques
        "div.suggestions", 
        "ul.autosuggest-suggestions",
        ".autocomplete-results", 
        ".autocomplete-items",
        "div[role='listbox']",
        ".modal .dropdown-menu",
        ".dropdown-content"
    ]
    
    # Méthode simple: d'abord essayons juste d'envoyer les touches flèche bas puis Entrée
    # Cette méthode est souvent plus fiable car elle ne dépend pas de la structure DOM
    try:
        logger.info("Tentative avec flèche bas + Entrée pour sélectionner la suggestion...")
        
        # Trouver un champ actif (qui a le focus)
        active_element = driver.switch_to.active_element
        if active_element:
            # Simuler flèche bas pour sélectionner la première suggestion
            active_element.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.7)  # Attendre que la sélection soit effective
            
            # Appuyer sur Entrée pour valider
            active_element.send_keys(Keys.ENTER)
            time.sleep(0.5)
            logger.info("Méthode touches clavier appliquée")
            return True
    except Exception as e:
        logger.warning(f"Méthode clavier échouée: {e}, essai méthodes alternatives")
    
    # Si la méthode simple échoue, essayons les méthodes basées sur le DOM
    try:
        logger.info("Recherche des suggestions via DOM...")
        
        # Essayer chaque sélecteur pour trouver la liste de suggestions
        suggestion_list = None
        for selector in suggestion_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for element in elements:
                        if element.is_displayed():
                            suggestion_list = element
                            logger.info(f"Liste de suggestions visible trouvée avec le sélecteur: {selector}")
                            break
                if suggestion_list:
                    break
            except:
                continue
                
        if not suggestion_list:
            # Essai avec attente
            for selector in suggestion_selectors:
                try:
                    suggestion_list = WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if suggestion_list.is_displayed():
                        logger.info(f"Liste de suggestions trouvée avec le sélecteur: {selector} après attente")
                        break
                except:
                    continue
        
        if not suggestion_list:
            # Essai avec JavaScript pour détecter les éléments visibles
            js_script = """
            return Array.from(document.querySelectorAll('.suggestions, .suggestions-container, [role="listbox"], .listbox'))
                   .filter(el => el.offsetParent !== null && window.getComputedStyle(el).display !== 'none')
                   .map(el => el.outerHTML);
            """
            suggestions_html = driver.execute_script(js_script)
            if suggestions_html:
                logger.info(f"Suggestions détectées via JavaScript: {len(suggestions_html)} éléments")
                # Essayons une simulation clavier plus directe
                active = driver.switch_to.active_element
                if active:
                    active.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)
                    active.send_keys(Keys.ENTER)
                    return True
            else:
                logger.warning("Aucune liste de suggestions visible détectée par JavaScript")
                return False
                
        # Différents sélecteurs possibles pour les éléments de suggestion
        item_selectors = [
            "li", 
            "div.suggestion-item",
            "[role='option']",
            ".dropdown-item",
            "a",
            "*"  # En dernier recours, tout élément enfant
        ]
        
        # Essayer chaque sélecteur pour les éléments
        suggestions = []
        for selector in item_selectors:
            try:
                items = suggestion_list.find_elements(By.CSS_SELECTOR, selector)
                visible_items = [item for item in items if item.is_displayed()]
                if visible_items:
                    suggestions = visible_items
                    logger.info(f"{len(visible_items)} options visibles trouvées avec le sélecteur: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Erreur avec sélecteur {selector}: {e}")
                continue
        
        if not suggestions:
            logger.warning("Aucune option visible trouvée dans la liste")
            # Derniers recours : flèche bas + Entrée
            active = driver.switch_to.active_element
            if active:
                active.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                active.send_keys(Keys.ENTER)
                return True
            return False
            
        logger.info(f"{len(suggestions)} suggestions visibles trouvées.")
        
        # Sélectionner le premier élément avec plusieurs méthodes
        first_item = suggestions[0]
        logger.info(f"Sélection de: {first_item.text if first_item.text.strip() else '[texte non visible]'}")
        
        # Méthode 1: JavaScript click avec mise en évidence
        try:
            driver.execute_script("""
                arguments[0].style.border = '2px solid red';
                arguments[0].scrollIntoView({block: 'center'});
                setTimeout(() => arguments[0].click(), 100);
            """, first_item)
            time.sleep(0.8)
            return True
        except Exception as e:
            logger.warning(f"Click JS amélioré échoué: {e}, essai méthode alternative")
            
        # Méthode 2: ActionChains complète (scroll, hover, pause, click)
        try:
            actions = ActionChains(driver)
            actions.move_to_element(first_item)
            actions.pause(0.3)
            actions.click()
            actions.perform()
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.warning(f"ActionChains complète échouée: {e}, essai méthode alternative")
            
        # Méthode 3: Send ENTER key après focus
        try:
            first_item.click()  # D'abord focus
            first_item.send_keys(Keys.ENTER)
            time.sleep(0.5)
            return True
        except Exception as e:
            logger.warning(f"ENTER key après focus échoué: {e}, dernier essai")
            
        # Méthode 4: Simulation complète clavier via élément actif
        try:
            active = driver.switch_to.active_element
            if active:
                active.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                active.send_keys(Keys.ENTER)
                return True
        except Exception as e:
            logger.warning(f"Simulation clavier finale échouée: {e}")
            return False
            
    except Exception as e:
        logger.warning(f"Erreur lors de la sélection de suggestion: {e}")
        
    # En dernier recours, essayer directement sur les champs
    try:
        for field_id in ['metier', 'lieu']:
            field = driver.find_element(By.ID, field_id)
            if field.is_enabled() and field.is_displayed():
                field.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                field.send_keys(Keys.ENTER)
                return True
    except:
        pass
        
    return False

def fill_field_with_autocomplete(driver, wait, field_id, value, max_retries=3):
    """Remplit un champ avec autocomplétion dans le modal."""
    logger.info(f"🎡 Remplissage du champ '{field_id}' avec '{value}'")
    
    # Différentes stratégies de sélecteurs pour trouver le champ dans le modal
    selectors = [
        f"#{field_id}",  # ID direct
        f"input[placeholder='Indiquez un métier ou une formation']",  # Par placeholder (comme vu dans la capture)
        ".modal-content input.autocomplete",  # Par structure modale 
        ".modal input[type='text']",  # Tout input text dans un modal
    ]
    
    for attempt in range(max_retries):
        logger.info(f"🔄 Tentative {attempt + 1}/{max_retries} pour le champ '{field_id}'")
        
        # Tenter chaque sélecteur jusqu'à ce qu'un fonctionne
        input_field = None
        for selector in selectors:
            try:
                input_field = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(f"Champ trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not input_field:
            logger.warning(f"Aucun champ trouvé à la tentative {attempt + 1}")
            continue
            
        try:
            # Cliquer pour activer le champ
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
            driver.execute_script("arguments[0].click();", input_field)
            time.sleep(0.5)
            
            # Effacer le contenu existant
            input_field.clear()
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)
            time.sleep(0.2)
            
            # Taper le texte caractère par caractère avec délai aléatoire
            for char in value:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            # Attendre que les suggestions apparaissent
            time.sleep(1.5)
            
            # Chercher les suggestions avec plusieurs sélecteurs possibles
            if select_suggestion(driver, wait):
                logger.info(f"✅ Valeur '{value}' saisie et suggestion sélectionnée")
                return True
            else:
                # Si pas de suggestion, essayer d'appuyer sur Entrée
                logger.warning("Pas de suggestion trouvée, essai avec la touche Entrée")
                input_field.send_keys(Keys.ENTER)
                time.sleep(1)
                return True
                
        except Exception as e:
            logger.warning(f"Erreur tentative {attempt+1}: {str(e)}")
            
    logger.error(f"❌ Échec du remplissage du champ '{field_id}' après {max_retries} tentatives")
    return False

def fill_field(driver, field_id, value, wait):
    """Remplit un champ avec une valeur donnée avec plusieurs méthodes en cas d'échec."""
    logger.info(f"🎡 Remplissage du champ '{field_id}' avec '{value}'")
    max_attempts = 4  # Plus de tentatives
    success = False
    original_value = value  # Garder la valeur d'origine
    
    # Capturer une image avant de commencer
    driver.save_screenshot(f'debug_screenshots/avant_remplissage_{field_id}.png')
    
    # Traitement spécial pour le champ métier
    if field_id.lower() == 'metier':
        logger.info("\n\n==== TRAITEMENT SPÉCIAL DU CHAMP MÉTIER ====\n")
        # Mettre l'écran en position pour voir le formulaire clairement
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Essayer de trouver et d'éliminer toute popup ou overlay qui pourrait interférer
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, ".fr-btn--close, .close-button, [aria-label*='fermer' i], [aria-label*='close' i]")
            for btn in close_buttons:
                if btn.is_displayed():
                    logger.info("Fermeture d'une popup ou overlay détecté...")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.5)
        except Exception:
            pass  # Ignorer les erreurs
    
    # Alternance des valeurs de recherche à essayer pour optimiser les chances de trouver des offres
    metier_values = []
    if field_id.lower() == 'metier':
        # Liste des valeurs à essayer pour le champ métier, par ordre de priorité
        if original_value.lower() == "commercial":
            metier_values = [
                "MÉTIER commercial",        # Utilise le marqueur MÉTIER explicite du site
                "CDI commercial",           # Les CDI sont uniquement pour les emplois
                "Offre emploi commercial",  # Très explicite pour des offres
                "Commercial alternance entreprise", # Alternance + entreprise
                "Commercial B to B",        # Version B2B (entreprise)
                "Commercial"               # Valeur de base en dernier recours
            ]
        elif original_value.lower() == "vendeur":
            metier_values = [
                "MÉTIER vendeur",          # Utilise le marqueur MÉTIER explicite
                "CDI vendeur",             # Les CDI sont uniquement pour les emplois
                "Offre emploi vendeur",    # Très explicite pour des offres
                "Vendeur alternance",      # Le terme alternance au lieu de formation
                "Vendeur magasin",         # Contexte professionnel
                "Vendeur"                  # En dernier recours
            ]
        else:
            # Pour d'autres métiers - stratégie générique optimisée pour les offres d'emploi
            metier_values = [
                f"MÉTIER {original_value}",          # Marqueur MÉTIER explicite du site
                f"CDI {original_value}",             # Les CDI sont uniquement pour des emplois
                f"Offre emploi {original_value}",    # Très explicite pour des offres
                f"{original_value} alternance entreprise", # Alternance + entreprise
                original_value                       # Valeur originale en dernier recours
            ]
    else:
        # Pour les autres champs, utiliser simplement la valeur d'origine
        metier_values = [original_value]
    
    for attempt in range(1, max_attempts + 1):
        # Changer de valeur à chaque tentative pour le champ métier
        if field_id.lower() == 'metier' and attempt <= len(metier_values):
            value = metier_values[attempt-1]
            logger.info(f"\n==> Tentative {attempt}/{max_attempts} avec la valeur: '{value}'\n")
        else:
            logger.info(f"\n==> Tentative {attempt}/{max_attempts} pour le champ '{field_id}'\n")

        logger.info(f"🔄 Tentative {attempt}/{max_attempts} pour le champ '{field_id}'")
        try:
            # Essayer une large gamme de sélecteurs
            field = None
            selectors = [
                f"#{field_id}",                        # ID direct
                f"input[name='{field_id}']",            # Attribut name
                f"input[id*='{field_id}']",            # ID contenant le nom du champ
                f"input[aria-label*='{field_id}']"     # Recherche partielle dans aria-label
            ]
            
            # Ajouter des sélecteurs spécifiques pour le champ métier
            if field_id.lower() == 'metier':
                selectors.extend([
                f"input[placeholder*='métier']",     # Placeholder contenant "métier"
                f"input[placeholder*='emploi']",     # Placeholder contenant "emploi"
                f"input[placeholder*='recherche']",   # Placeholder générique de recherche
                f"input[aria-label*='{field_id}']"     # Recherche partielle dans aria-label
                ])
            
            # Ajouter des sélecteurs plus généraux à la fin
            selectors.extend([
                f"input[aria-label*='{field_id}']",     # Recherche partielle dans aria-label
                f"input[id*='{field_id}']",            # ID contenant le nom du champ
                "input.fr-input",                      # Classe spécifique fr-input
                "input[type='text']"                   # Tout input de type text
            ])
            
            # Ajouter des sélecteurs plus génériques pour le champ métier
            if field_id.lower() == 'metier':
                selectors.extend([
                    "input.react-autosuggest__input",    # React autosuggest
                    ".fr-search-bar input",             # Barre de recherche FR
                    "input[type='search']"              # Input de type search
                ])
                
            for selector in selectors:
                try:
                    field_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if field_elements:
                        # Si plusieurs éléments sont trouvés, prendre celui qui est visible
                        for el in field_elements:
                            if el.is_displayed() and el.is_enabled():
                                field = el
                                logger.info(f"Champ trouvé avec le sélecteur: {selector}")
                                break
                        if field:
                            break
                except Exception:
                    continue
                    
            # Si toujours pas trouvé, essayer avec XPath
            if not field:
                xpath_selectors = [
                    f"//input[@id='{field_id}']",
                    f"//input[@name='{field_id}']",
                    f"//input[contains(@id, '{field_id}')]",
                    f"//input[contains(@name, '{field_id}')]",
                    f"//input[contains(@placeholder, '{field_id}')]",
                    f"//input[contains(@aria-label, '{field_id}')]",
                    "//input[@type='text']"
                ]
                
                # XPath spécifique pour le champ métier
                if field_id.lower() == 'metier':
                    xpath_selectors.extend([
                        "//input[contains(@placeholder, 'métier') or contains(@placeholder, 'recherche')]",
                        "//label[contains(translate(text(), 'MÉTIER', 'métier'), 'métier')]/following::input[1]",
                        "//input[ancestor::*[contains(@class, 'search') or contains(@id, 'search')]]"
                    ])
                
                for xpath in xpath_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        if elements:
                            for el in elements:
                                if el.is_displayed() and el.is_enabled():
                                    field = el
                                    logger.info(f"Champ trouvé avec le XPath: {xpath}")
                                    break
                            if field:
                                break
                    except Exception:
                        continue
            
            if not field:
                logger.warning(f"Impossible de trouver le champ '{field_id}' - tentative {attempt}")
                continue
            
            # MÉTHODES AGRESSIVES POUR MÉTIER
            if field_id.lower() == 'metier':
                logger.info("🔍 Utilisation de méthodes agressives pour le champ métier")
                
                # 1. Mettre en évidence visuellement le champ pour déboguer
                driver.execute_script("arguments[0].style.border='3px solid red';", field)
                driver.save_screenshot('debug_screenshots/metier_field_highlighted.png')
                
                # 2. Force focus avant tout
                driver.execute_script("arguments[0].focus();", field)
                time.sleep(0.5)
                
                # 3. Forcer l'effacement avec plusieurs méthodes
                try:
                    # Méthode 1: Clear standard
                    field.clear()
                    # Méthode 2: Sélectionner tout et supprimer
                    field.send_keys(Keys.CONTROL + "a")
                    field.send_keys(Keys.DELETE)
                    # Méthode 3: JavaScript
                    driver.execute_script("arguments[0].value = '';", field)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'effacement du champ: {e}")
                
                time.sleep(0.5)
                
                # 4. Vérifier que le champ est bien vide
                if field.get_attribute("value"):
                    logger.warning("Le champ n'est pas vide après tentative d'effacement")
                    driver.execute_script("arguments[0].value = '';", field)
                
                # 5. Saisie caractère par caractère LENTE
                logger.info(f"Saisie lente de la valeur: '{value}'")
                for char in value:
                    # Envoyer chaque caractère avec une pause
                    field.send_keys(char)
                    time.sleep(0.2)  # Pause plus longue entre chaque caractère
                    
                    # Vérifier que le caractère a bien été saisi
                    current_value = field.get_attribute("value")
                    logger.info(f"  -> Valeur actuelle: '{current_value}'")
                
                # 6. Pause significative pour laisser apparaitre les suggestions
                time.sleep(2)  # Pause beaucoup plus longue
                
                # 7. Capture d'écran pour voir si des suggestions sont apparues
                driver.save_screenshot('debug_screenshots/apres_saisie_metier.png')
                
                # 8. Vérifier que la valeur est bien saisie
                field_value = field.get_attribute("value")
                logger.info(f"Valeur finale du champ: '{field_value}'")
                
                if field_value != value:
                    # Si le champ n'a pas la valeur attendue, essayer JavaScript
                    logger.warning(f"La valeur du champ ({field_value}) ne correspond pas à la valeur attendue ({value})")
                    driver.execute_script(f"arguments[0].value = '{value}';", field)
                    # Déclencher événements pour simuler une saisie réelle
                    driver.execute_script("""
                        var el = arguments[0];
                        var evt = new Event('input', { bubbles: true });
                        el.dispatchEvent(evt);
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    """, field)
                    time.sleep(1)
            else:
                # Pour les autres champs, méthode standard
                field.clear()
                time.sleep(0.3)
                
                # Remplir le champ caractère par caractère avec pause
                for char in value:
                    field.send_keys(char)
                    time.sleep(0.1)  # Petite pause entre chaque caractère
                
                time.sleep(1)  # Pause pour laisser les suggestions apparaitre
            
            # Traiter spécifiquement le champ 'metier' pour sélectionner une suggestion de type 'MÉTIER' et pas 'FORMATION'
            if field_id.lower() == 'metier':
                logger.info("\n\n==== RECHERCHE DES SUGGESTIONS DE TYPE MÉTIER ====\n")
                
                # Déclencher des événements supplémentaires pour s'assurer que les suggestions s'affichent
                try:
                    # Simuler un clic sur le champ
                    field.click()
                    # Simuler une pression sur la touche flèche bas pour faire apparaître les suggestions
                    field.send_keys(Keys.ARROW_DOWN)
                    # Simuler des événements JavaScript pour déclencher l'affichage des suggestions
                    driver.execute_script("""
                        var el = arguments[0];
                        el.dispatchEvent(new Event('focus', { bubbles: true }));
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    """, field)
                except Exception as e:
                    logger.warning(f"Erreur lors du déclenchement d'événements pour afficher les suggestions: {e}")
                
                # Pause longue pour s'assurer que les suggestions apparaissent
                time.sleep(3)  # Attente plus longue pour les suggestions
                
                # Capture d'écran pour voir si des suggestions sont apparues
                driver.save_screenshot('debug_screenshots/suggestions_metier_avant_selection.png')
                
                # MÉTHODE ULTRA-ROBUSTE POUR SÉLECTIONNER LES SUGGESTIONS
                # Stratégie: Utiliser multiples approches, du plus spécifique au plus générique
                
                # 1. Capture d'écran de diagnostic avant toute action
                driver.save_screenshot('debug_screenshots/avant_selection_suggestions.png')
                logger.info("\n🔎 NOUVELLES MÉTHODES DE SÉLECTION DES SUGGESTIONS\n")
                
                # 2. Forcer l'apparition des suggestions avec multiples techniques
                suggestion_found = False
                
                # APPROCHE 1: Simulation d'interaction utilisateur très explicite
                try:
                    logger.info("MÉTHODE 1: Simulation complète d'interaction utilisateur")
                    # Effacer et remplir à nouveau le champ pour déclencher des suggestions fraîches
                    field.clear()
                    time.sleep(1)
                    # Saisir caractère par caractère avec délai important
                    for char in value:
                        field.send_keys(char)
                        time.sleep(0.3)
                    
                    # Encourager l'apparition des suggestions
                    time.sleep(1)
                    field.click()
                    field.send_keys(Keys.END)  # Aller à la fin du texte
                    time.sleep(1)
                    
                    # Tenter une touche flèche bas pour activer la première suggestion
                    field.send_keys(Keys.ARROW_DOWN)
                    time.sleep(1)
                    driver.save_screenshot('debug_screenshots/suggestions_apres_fleche_bas.png')
                    
                    # Valider la suggestion avec Entrée
                    field.send_keys(Keys.ENTER)
                    time.sleep(1)
                    
                    suggestion_found = True
                    logger.info("✅ Suggestion sélectionnée avec la méthode d'interaction complète")
                except Exception as e:
                    logger.warning(f"Échec méthode 1: {e}")
                
                # APPROCHE 2: Sélection via JavaScript si la première méthode échoue
                if not suggestion_found:
                    try:
                        logger.info("MÉTHODE 2: Sélection via JavaScript direct")
                        # Script JS avancé pour trouver et sélectionner une suggestion
                        js_script = """
                        function findAndSelectSuggestion() {
                            // Trouver tous les éléments qui pourraient être des suggestions
                            var potentialSuggestions = [];
                            
                            // Sélecteurs spécifiques à React et aux composants FR Design System
                            var selectors = [
                                '.fr-autocomplete__menu-item',
                                '.react-autosuggest__suggestion',
                                '[role="option"]',
                                '.suggestions li',
                                'ul li[role="option"]',
                                'div[role="listbox"] div',
                                '.dropdown-item',
                                '.autocomplete-result',
                                '.results-item',
                                'ul.autocomplete-results li',
                                'div.suggestion-item'
                            ];
                            
                            // Essayer chaque sélecteur
                            for (var i = 0; i < selectors.length; i++) {
                                var elements = document.querySelectorAll(selectors[i]);
                                if (elements && elements.length > 0) {
                                    console.log('Trouvé ' + elements.length + ' suggestions avec ' + selectors[i]);
                                    
                                    // Chercher d'abord un élément qui contient 'métier' ou 'emploi' mais pas 'formation'
                                    for (var j = 0; j < elements.length; j++) {
                                        var text = elements[j].innerText.toLowerCase();
                                        if (text && 
                                           (text.includes('métier') || text.includes('emploi') || 
                                            text.includes('commercial') || text.includes('vendeur')) && 
                                           !text.includes('formation') && !text.includes('diplôme')) {
                                            
                                            // C'est une suggestion de type métier, la cliquer
                                            console.log('MÉTIER TROUVÉ: ' + text);
                                            elements[j].click();
                                            return 'Suggestion métier sélectionnée: ' + text;
                                        }
                                    }
                                    
                                    // Si pas trouvé de suggestion métier explicite, prendre la première
                                    if (elements[0]) {
                                        console.log('Sélection première suggestion: ' + elements[0].innerText);
                                        elements[0].click();
                                        return 'Première suggestion sélectionnée: ' + elements[0].innerText;
                                    }
                                }
                            }
                            
                            // Recherche générique si les sélecteurs spécifiques échouent
                            var allElements = document.querySelectorAll('*');
                            var visibleElements = [];
                            
                            // Filtrer uniquement les éléments visibles qui semblent être des suggestions
                            for (var i = 0; i < allElements.length; i++) {
                                var el = allElements[i];
                                var style = window.getComputedStyle(el);
                                var rect = el.getBoundingClientRect();
                                
                                // Élément visible et semble être une suggestion (petit élément avec du texte)
                                if (el.innerText && 
                                    style.display !== 'none' && 
                                    style.visibility !== 'hidden' && 
                                    rect.height > 0 && rect.height < 100 && 
                                    rect.width > 0 && rect.width < 500) {
                                    
                                    visibleElements.push(el);
                                }
                            }
                            
                            // Trier les éléments par probabilité d'être une suggestion
                            visibleElements.sort(function(a, b) {
                                var scoreA = 0;
                                var scoreB = 0;
                                
                                var textA = a.innerText.toLowerCase();
                                var textB = b.innerText.toLowerCase();
                                
                                // Donner un score basé sur le contenu
                                if (textA.includes('métier')) scoreA += 5;
                                if (textA.includes('emploi')) scoreA += 5;
                                if (textA.includes('commercial')) scoreA += 3;
                                if (textA.includes('formation')) scoreA -= 10;
                                
                                if (textB.includes('métier')) scoreB += 5;
                                if (textB.includes('emploi')) scoreB += 5;
                                if (textB.includes('commercial')) scoreB += 3;
                                if (textB.includes('formation')) scoreB -= 10;
                                
                                return scoreB - scoreA;
                            });
                            
                            // Sélectionner le meilleur élément
                            if (visibleElements.length > 0) {
                                console.log('Meilleur élément trouvé: ' + visibleElements[0].innerText);
                                visibleElements[0].click();
                                return 'Élément sélectionné: ' + visibleElements[0].innerText;
                            }
                            
                            return 'Aucune suggestion trouvée';
                        }
                        
                        // Exécuter la fonction
                        return findAndSelectSuggestion();
                        """
                        
                        # Exécuter le script et enregistrer le résultat
                        js_result = driver.execute_script(js_script)
                        logger.info(f"Résultat JavaScript: {js_result}")
                        
                        # Si le script a trouvé une suggestion, marquer comme succès
                        if not 'aucune suggestion' in js_result.lower():
                            suggestion_found = True
                            logger.info("✅ Suggestion sélectionnée via JavaScript")
                    except Exception as e:
                        logger.warning(f"Échec méthode 2: {e}")
                
                # APPROCHE 3: Méthode brutale - Séquence de touches si les autres méthodes échouent
                if not suggestion_found:
                    try:
                        logger.info("MÉTHODE 3: Séquence de touches brutale")
                        # Effacer et saisir à nouveau
                        field.clear()
                        time.sleep(0.5)
                        
                        # Ajouter explicitement "Emploi" au début
                        field.send_keys("Emploi " + value)
                        time.sleep(1.5)
                        
                        # Séquence de touches
                        field.send_keys(Keys.TAB)  # Sortir du champ
                        time.sleep(0.5)
                        field.click()  # Revenir au champ
                        time.sleep(0.5)
                        field.send_keys(Keys.ARROW_DOWN)  # 1ère suggestion
                        time.sleep(0.5)
                        field.send_keys(Keys.ARROW_DOWN)  # 2ème suggestion (souvent après un titre)
                        time.sleep(0.5)
                        field.send_keys(Keys.ENTER)
                        suggestion_found = True
                        logger.info("✅ Méthode brutale appliquée")
                    except Exception as e:
                        logger.warning(f"Échec méthode 3: {e}")
                
                # Capture d'écran après toutes les tentatives
                driver.save_screenshot('debug_screenshots/apres_selection_suggestions_final.png')
                
                if not suggestion_found:
                    logger.warning("⚠️ AUCUNE MÉTHODE N'A RÉUSSI À SÉLECTIONNER UNE SUGGESTION")
                    # Dernière tentative désespérée - simuler un TAB puis ENTER
                    try:
                        field.send_keys(Keys.TAB)
                        time.sleep(0.5)
                        field.send_keys(Keys.ENTER)
                    except Exception as e:
                        logger.error(f"Erreur lors de la dernière tentative: {e}")
                    
                # Fin des trois approches - derniers logs
                logger.info("Fin de la tentative de sélection des suggestions")
            else:
                # Pour les autres champs, utiliser la méthode standard
                logger.info("Tentative avec flèche bas + Entrée pour sélectionner la suggestion...")
                try:
                    field.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)
                    field.send_keys(Keys.ENTER)
                    logger.info("Méthode touches clavier appliquée")
                except Exception as e:
                    logger.error(f"Impossible de sélectionner une suggestion: {str(e)}")
                    pass
                
            logger.info("Méthode de sélection des suggestions appliquée")
            
            time.sleep(1)  # Attendre après la sélection
            
            # Capture d'écran après remplissage
            driver.save_screenshot(f'debug_screenshots/apres_remplissage_{field_id}.png')
            
            success = True
            logger.info(f"✅ Valeur '{value}' saisie et suggestion sélectionnée")
            break
            
        except Exception as e:
            logger.warning(f"Erreur lors du remplissage du champ '{field_id}': {str(e)}")
            time.sleep(1)
    
    if not success:
        logger.error(f"\u274c Échec du remplissage du champ '{field_id}' après {max_attempts} tentatives")
    
    return success

# Fin des trois approches - derniers logs
logger.info("Fin de la tentative de sélection des suggestions")

# --- Fonctions de postulation et capture importées depuis les modules externes ---
# Voir postuler_functions.py et capture_functions.py

# --- Processus de scraping principal ---

def run_scraper(user_data):
    logger.info(f"Lancement du scraper pour : {user_data['email']}")
    driver = None
    try:
        # Créer le WebDriver avec ouverture auto des DevTools
        driver = setup_driver()
        if not driver:
            logger.error("Impossible de créer le WebDriver. Arrêt du script.")
            return

        # Configuration de l'attente explicite
        wait = WebDriverWait(driver, 20)
        short_wait = WebDriverWait(driver, 5)

        # Accès à la page
        url = "https://www.alternance.emploi.gouv.fr/recherches-offres-formations"
        logger.info(f"Accès à l'URL : {url}")
        driver.get(url)
        
        # Les DevTools s'ouvrent automatiquement maintenant grâce à notre setup
        logger.info("DevTools devraient maintenant être ouverts automatiquement")
        
        # Pause pour s'assurer que la page est complètement chargée
        time.sleep(3)

        # Gestion des cookies
        try:
            cookie_button = short_wait.until(EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2")))
            cookie_button.click()
            logger.info("Bannière de cookies acceptée.")
        except Exception as e:
            logger.warning(f"Bannière de cookies non trouvée ou déjà acceptée: {e}")

        try:
            # Étape 1: Basculement et traitement de l'iframe contenant le formulaire
            # Identifier l'iframe contenant le formulaire
            logger.info("Recherche de l'iframe...")
            iframe = None
            try:
                iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id*='recherche']")))  # L'iframe contenant le mot 'recherche' dans l'ID
                logger.info("Iframe trouvé.")
            except TimeoutException:
                try: 
                    iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                    logger.info("Iframe trouvé via tag name.")
                except TimeoutException:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    if iframes:
                        iframe = iframes[0]  # Prendre le premier iframe comme fallback
                        logger.info(f"Premier iframe pris par défaut. Total iframes: {len(iframes)}")
                    else:
                        logger.error("Aucun iframe trouvé sur la page")
                        raise Exception("Erreur: Page mal chargée, aucun iframe disponible")

            if not iframe:
                logger.error("Iframe non trouvé malgré les tentatives")
                driver.save_screenshot('no_iframe_error.png')
                with open('page_source_no_iframe.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                raise Exception("Erreur: Iframe contenant le formulaire non trouvé")
            
            # Basculer vers l'iframe
            logger.info("Basculement vers l'iframe...")
            driver.switch_to.frame(iframe)
            logger.info("Basculement vers l'iframe réussi.")
            
            # Pause pour laisser le contenu de l'iframe se charger complètement
            logger.info("Attente du chargement de l'iframe...")
            time.sleep(4)
            
            # Code pour forcer l'affichage du formulaire modal en se basant sur l'inspection manuelle
            logger.info("Tentative d'activation du formulaire par simulation d'inspection...")
            
            # Script JavaScript qui simule exactement ce que fait l'inspection pour révéler le formulaire modal
            reveal_modal_script = """
            (function() {
                console.log('Début de la simulation d\'inspection');
                
                // 1. Simuler les variables globales DevTools
                window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = { 
                    isDisabled: false,
                    supportsFiber: true,
                    renderers: new Map(),
                    inject: function() {},
                    hookNames: new Map(),
                    connected: true
                };
                
                // 2. Forcer l'affichage des éléments cachés dans le modal
                var modalElement = document.querySelector('.fr-modal__body');
                if (modalElement) {
                    console.log('Modal trouvé, force affichage');
                    modalElement.style.display = 'block';
                } else {
                    console.log('Modal non trouvé');
                }
                
                // 3. Créer le formulaire modal s'il n'existe pas
                var formContainer = document.querySelector('.fr-modal__content');
                if (!formContainer) {
                    console.log('Conteneur de formulaire non trouvé - tentative création');
                    // Forcer la réinitialisation des éléments DOM cachés
                    document.body.innerHTML += '<div style="display:none" id="temp-trigger"></div>';
                    document.getElementById('temp-trigger').click();
                }
                
                // 4. Simuler l'état actif des DevTools
                window.devtools = { isOpen: true, orientation: 'vertical' };
                document.__devTools = true;
                
                // 5. Déclencher des événements qui peuvent activer des comportements JavaScript
                document.dispatchEvent(new CustomEvent('devtoolschange', { detail: { isOpen: true } }));
                document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }));
                
                // 6. Vérifier et révéler les champs du formulaire
                var metierField = document.getElementById('metier');
                var formFields = document.querySelectorAll('input, select, button');
                
                if (metierField) {
                    console.log('Champ métier trouvé, activation...');
                    metierField.style.display = 'block';
                    metierField.style.visibility = 'visible';
                    metierField.focus();
                    
                    // Récupérer l'état actuel du formulaire pour diagnostique
                    return {
                        success: true, 
                        formFound: !!metierField,
                        formFieldsCount: formFields.length,
                        modalVisible: !!modalElement
                    };
                } else {
                    // Retourner information sur le DOM actuel
                    return { 
                        success: false, 
                        formFound: false,
                        bodyContent: document.body.innerHTML.substring(0, 500) + '...',
                        formFields: formFields.length
                    };
                }
            })();
            """
            
            try:
                # Exécuter le script pour révéler le formulaire
                result = driver.execute_script(reveal_modal_script)
                logger.info(f"Résultat de l'activation: {result}")
                
                # Pause pour observer si le formulaire est visible
                time.sleep(2)
                
                # Tenter de trouver et cliquer sur le champ métier
                try:
                    metier_field = driver.find_element(By.ID, "metier")
                    logger.info("Champ métier trouvé! Simulation d'un clic...")
                    driver.execute_script("arguments[0].click();", metier_field)
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"Champ métier non trouvé après activation: {e}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'activation du formulaire: {e}")
                
                # Pause pour observer le résultat
                time.sleep(2)
                
                # Maintenant, essayons de remplir les champs directement, puisque nous avons activé le formulaire
                logger.info("Tentative de remplissage direct du champ métier...")
                
                try:
                    # Recherche du champ métier via ID
                    metier_field = wait.until(EC.presence_of_element_located((By.ID, "metier")))
                    logger.info("Champ métier trouvé par ID")
                    
                    # Utilisation du script JavaScript pour insérer la valeur et déclencher les événements nécessaires
                    fill_input_script = """
                    (function() {
                        var input = document.getElementById('metier');
                        if (input) {
                            // Mettre le focus et remplir le champ
                            input.focus();
                            input.value = arguments[0];
                            
                            // Déclencher les événements nécessaires pour activer l'autocomplétion
                            input.dispatchEvent(new Event('focus', { bubbles: true }));
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return { success: true, value: input.value };
                        }
                        return { success: false, error: 'Champ métier non trouvé' };
                    })();
                    """
                    
                    # Exécution du script avec la valeur du métier
                    result = driver.execute_script(fill_input_script, user_data['search_query'])
                    logger.info(f"Résultat du remplissage du champ métier: {result}")
                    
                    # Attendre que les suggestions apparaissent
                    time.sleep(2)
                    
                    # Sélectionner la première suggestion (via touche flèche bas puis Entrée)
                    select_suggestion_script = """
                    (function() {
                        var input = document.getElementById('metier');
                        if (input) {
                            // Simuler flèche bas pour sélectionner la première suggestion
                            input.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'ArrowDown',
                                code: 'ArrowDown',
                                keyCode: 40,
                                which: 40,
                                bubbles: true
                            }));
                            
                            // Petite pause
                            setTimeout(function() {
                                // Simuler Entrée pour valider la suggestion
                                input.dispatchEvent(new KeyboardEvent('keydown', {
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true
                                }));
                            }, 500);
                            
                            return true;
                        }
                        return false;
                    })();
                    """
                    
                    # Attendre que les suggestions apparaissent puis sélectionner
                    time.sleep(1)
                    driver.execute_script(select_suggestion_script)
                    logger.info("Sélection de la suggestion effectuée")
                    time.sleep(2)
                    
                    # Même procédure pour le champ lieu
                    logger.info("Tentative de remplissage du champ lieu...")
                    fill_lieu_script = """
                    (function() {
                        var input = document.getElementById('lieu');
                        if (input) {
                            // Mettre le focus et remplir le champ
                            input.focus();
                            input.value = arguments[0];
                            
                            // Déclencher les événements
                            input.dispatchEvent(new Event('focus', { bubbles: true }));
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return { success: true, value: input.value };
                        }
                        return { success: false, error: 'Champ lieu non trouvé' };
                    })();
                    """
                    
                    driver.execute_script(fill_lieu_script, user_data['location'])
                    logger.info("Remplissage du champ lieu effectué")
                    time.sleep(2)
                    
                    # Sélectionner suggestion lieu
                    driver.execute_script(select_suggestion_script.replace('metier', 'lieu'))
                    logger.info("Sélection de la suggestion lieu effectuée")
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erreur lors du remplissage direct des champs: {e}")
                    # Continuer avec l'approche standard si l'approche directe échoue
                
                # Approche finale: Activation complète du formulaire 
                logger.info("Activation complète du formulaire avec révélation des éléments cachés...")
                
                # Script combiné pour activer tous les éléments du formulaire
                complete_activation_script = """
                (function() {
                    console.log('Début activation complète du formulaire...');
                    
                    // Simuler l'environnement DevTools
                    window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = { 
                        isDisabled: false,
                        supportsFiber: true,
                        renderers: new Map(),
                        inject: function() {},
                        hookNames: new Map(),
                        connected: true
                    };
                    window.devtools = { isOpen: true, orientation: 'vertical' };
                    document.__devTools = true;
                    window.__REDUX_DEVTOOLS_EXTENSION__ = function() { return function() { return arguments[0]; } };
                    
                    // API Chrome DevTools simulée
                    window.chrome = window.chrome || {};
                    window.chrome.devtools = {
                        inspectedWindow: { eval: function() {} },
                        network: { getHAR: function() {} }
                    };
                    
                    // Déclencher des événements d'activation
                    document.dispatchEvent(new CustomEvent('devtoolschange', { detail: { isOpen: true } }));
                    document.dispatchEvent(new Event('DOMContentLoaded', { bubbles: true }));
                    document.dispatchEvent(new Event('readystatechange', { bubbles: true }));
                    window.dispatchEvent(new Event('load', { bubbles: true }));
                    
                    // Révéler les éléments cachés du DOM
                    var revealed = 0;
                    document.querySelectorAll('*').forEach(function(el) {
                        if (getComputedStyle(el).display === 'none') {
                            console.log('Révélation élément caché:', el.tagName);
                            el.style.display = el.tagName === 'INPUT' ? 'inline-block' : 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                            revealed++;
                        }
                    });
                    
                    // Traiter spécifiquement les éléments de formulaire
                    var metierField = document.getElementById('metier');
                    var lieuField = document.getElementById('lieu');
                    var formFields = [metierField, lieuField];
                    
                    // Activer et rendre visibles les champs du formulaire
                    formFields.forEach(function(field) {
                        if (field) {
                            field.style.display = 'block';
                            field.style.visibility = 'visible';
                            field.disabled = false;
                            field.setAttribute('data-activated', 'true');
                        }
                    });
                    
                    return { 
                        success: true, 
                        revealed: revealed, 
                        metierFound: !!metierField,
                        lieuFound: !!lieuField,
                        formCount: document.forms.length 
                    };
                })();
                """
                
                try:
                    # Exécuter le script d'activation complète
                    activation_result = driver.execute_script(complete_activation_script)
                    logger.info(f"Résultat de l'activation complète: {activation_result}")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'activation complète du formulaire: {e}")
                
                # Tentative de remplissage des champs après activation complète
                logger.info("Tentative de remplissage des champs après activation complète...")
                try:
                    # Ne pas remplir les champs ici pour éviter la double saisie
                    # Ces champs seront remplis plus tard dans le flux principal
                    logger.info("Activation du formulaire terminée, les champs seront remplis dans l'étape suivante")
                except Exception as e:
                    logger.error(f"Erreur lors du remplissage après activation complète: {e}")
                    driver.save_screenshot('form_filling_error.png')
                    
                time.sleep(2)
                
                # Pause pour donner le temps au JavaScript de prendre effet
                time.sleep(5)
                
                # Effectuer un clic simulant une interaction humaine pour réveiller le formulaire
                try:
                    # Essayer de trouver un élément visible et cliquer dessus
                    visible_elements = driver.find_elements(By.CSS_SELECTOR, "body *:not(script):not(style):not(meta)")
                    for el in visible_elements[:5]:  # Limiter aux 5 premiers éléments pour éviter de parcourir tout le DOM
                        try:
                            if el.is_displayed():
                                logger.info(f"Clic sur un élément visible: {el.tag_name}")
                                el.click()
                                break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Erreur lors de la tentative de clic sur un élément visible: {e}")
                
                # Pause supplémentaire
                time.sleep(3)
                
                # Décocher la case "Formations" si elle est cochée - Avec plusieurs tentatives
                try:
                    logger.info("IMPORTANT: Tentative de décocher la case Formations...")
                    time.sleep(1)  # Attendre que tout soit chargé
                    
                    # Méthode 1: Utiliser la fonction existante
                    success = uncheck_formations_checkbox(driver, wait)
                    
                    # Méthode 2: JavaScript direct et plus agressif pour décocher TOUTES les cases Formations
                    js_code = """
                    console.log('Décochage force des cases formations');
                    // Approche 1: par attribut name
                    var checkboxes = document.querySelectorAll('input[name="formations"][type="checkbox"]');
                    console.log('Checkboxes formations trouvées:', checkboxes.length);
                    
                    // Décocher toutes les cases qui correspondent
                    checkboxes.forEach(function(checkbox) {
                        if (checkbox.checked || checkbox.getAttribute('checked') === 'true') {
                            console.log('Case à décocher trouvée');
                            checkbox.checked = false;
                            checkbox.setAttribute('checked', 'false');
                            checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    });
                    
                    // Approche 2: par texte du label
                    var labels = document.querySelectorAll('label');
                    labels.forEach(function(label) {
                        if (label.textContent.includes('Formation')) {
                            var input = document.getElementById(label.getAttribute('for'));
                            if (input && (input.checked || input.getAttribute('checked') === 'true')) {
                                console.log('Case formation trouvée via label');
                                input.checked = false;
                                input.setAttribute('checked', 'false');
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }
                    });
                    
                    // Approche 3: très agressive, cibler toute case à cocher avec un label contenant formation
                    var allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
                    console.log('Total checkboxes:', allCheckboxes.length);
                    allCheckboxes.forEach(function(cb) {
                        var parentText = cb.parentElement ? cb.parentElement.textContent.toLowerCase() : '';
                        if (parentText.includes('formation') && cb.checked) {
                            console.log('Case formation trouvée via parent');
                            cb.checked = false;
                            cb.click();
                        }
                    });
                    
                    return 'Décochage forcé des cases Formations terminé';
                    """
                    
                    result = driver.execute_script(js_code)
                    logger.info(f"Résultat du décochage forcé: {result}")
                    
                    # Méthode 3: Décoche directe par Sélecteur CSS
                    try:
                        # Essayer de trouver directement les cases à décocher
                        formations_checkboxes = driver.find_elements(By.CSS_SELECTOR, ".filter-checkbox input[type='checkbox']")
                        for cb in formations_checkboxes:
                            try:
                                parent = cb.find_element(By.XPATH, "./..") 
                                parent_text = parent.text.lower()
                                if 'formation' in parent_text and cb.is_selected():
                                    logger.info("Case Formation trouvée directement, tentative de décochage...")
                                    driver.execute_script("arguments[0].click();", cb)
                            except Exception as inner_e:
                                pass
                    except Exception as e:
                        logger.warning(f"Erreur lors de la recherche directe de cases à décocher: {e}")
                    
                    # Prendre une capture d'écran après le décochage pour vérification
                    driver.save_screenshot('debug_screenshots/apres_decochage.png')
                    logger.info("Capture d'écran enregistrée après le décochage")
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de la tentative de décocher la case Formations: {e}")
                    driver.save_screenshot('debug_screenshots/erreur_decochage.png')
                    
                # Pause supplémentaire
                time.sleep(3)
                
                # Vérifier si les champs du formulaire sont présents
                try:
                    metier_field = wait.until(EC.presence_of_element_located((By.ID, "metier")))
                    logger.info("✅ Le champ métier est visible.") 
                except Exception as e:
                    logger.warning(f"Le champ métier n'est pas visible: {e}")
                    logger.info("Essai de localisation par d'autres sélecteurs...")
                    # Essayer d'autres sélecteurs
                    try:
                        metier_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#metier, input[name='metier'], input[placeholder*='métier']")))
                        logger.info("✅ Champ métier trouvé avec un sélecteur alternatif!")
                    except Exception as e2:
                        logger.error(f"Impossible de trouver le champ métier avec des sélecteurs alternatifs: {e2}")
                        # Sauvegarde du DOM pour analyse
                        with open('etat_iframe.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        logger.info("DOM de l'iframe sauvegardé dans 'etat_iframe.html'")
        except Exception as e:
            logger.error(f"Erreur lors de l'interaction avec l'iframe: {e}")
            # Revenir au contenu principal
            driver.switch_to.default_content()
            with open('etat_page_principale.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("DOM de la page principale sauvegardé dans 'etat_page_principale.html'")
            raise  # Relancer l'exception pour indiquer qu'il y a eu un problème grave
        
        # Pause avant de commencer le remplissage
        time.sleep(2)
        
        # Décocher la case "Formations" si elle est cochée
        uncheck_formations_checkbox(driver, wait)
        
        # Étape 3: Remplissage des champs avec notre fonction améliorée
        logger.info("Début du remplissage des champs du formulaire...")
        
        # Vérifier la présence des champs principal avant de commencer
        try:
            # Utiliser les sélecteurs variables pour trouver le champ métier
            metier_selectors = [
                "#metier", 
                "input[placeholder*='métier']",
                ".modal input[type='text']:first-child",
                "input.fr-input"
            ]
            
            metier_input = None
            for selector in metier_selectors:
                try:
                    metier_input = short_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"Champ métier trouvé avec le sélecteur: {selector}")
                    break
                except:
                    continue
            
            if not metier_input:
                logger.warning("Champ métier introuvable avec les sélecteurs standard")
        except Exception as e:
            logger.error(f"Problème lors de la recherche des champs: {e}")
        
        # Tentative de remplissage du champ métier
        if not fill_field_with_autocomplete(driver, wait, 'metier', user_data['search_query']):
            logger.error("Impossible de remplir le champ métier")
            raise Exception("Erreur lors de la tentative de soumission du formulaire: Échec du remplissage du champ 'métier'")
                
        # Pause entre les champs
        time.sleep(1.5)
            
        # Tentative de remplissage du champ lieu
        if not fill_field_with_autocomplete(driver, wait, 'lieu', user_data['location']):
            logger.warning("Impossible de remplir le champ lieu, essai de continuer sans")
            
        # Pause avant soumission 
        time.sleep(1)
            
        # Étape 4: Soumission du formulaire - multiple sélecteurs et stratégies
        logger.info("Préparation à la soumission du formulaire...")
            
        # Liste des sélecteurs possibles pour le bouton de soumission
        submit_button_selectors = [
            "button[title=\"C'est parti\"]",
            ".fr-btn--primary",
            "button.search-button",
            "button[type='submit']",
            "input[type='submit']",
            ".modal-content button",
            "button:contains('partir')"
        ]
            
        # Tentative avec chaque sélecteur
        submit_button = None
        for selector in submit_button_selectors:
            try:
                submit_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Bouton de soumission trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not submit_button:
            # Si aucun bouton n'est trouvé avec les sélecteurs, essayer avec le texte du bouton
            try:
                # Recherche par texte (moins fiable mais solution de secours)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    text = button.text or ""
                    btn_class = button.get_attribute("class") or ""
                    if "parti" in text or "search" in text.lower() or "submit" in btn_class.lower():
                        submit_button = button
                        logger.info(f"Bouton de soumission trouvé avec le texte: {button.text}")
                        break
            except Exception as e:
                logger.warning(f"Tentative de recherche par texte échouée: {e}")
        
        # Pause avant soumission 
        time.sleep(1)
        
        # Étape 4: Soumission du formulaire - multiple sélecteurs et stratégies
        logger.info("Préparation à la soumission du formulaire...")
        
        # Liste des sélecteurs possibles pour le bouton de soumission
        submit_button_selectors = [
            "button[title=\"C'est parti\"]",
            ".fr-btn--primary",
            "button.search-button",
            "button[type='submit']",
            "input[type='submit']",
            ".modal-content button",
            "button:contains('partir')"
        ]
        
        # Tentative avec chaque sélecteur
        submit_button = None
        for selector in submit_button_selectors:
            try:
                submit_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                logger.info(f"Bouton de soumission trouvé avec le sélecteur: {selector}")
                break
            except:
                continue
        
        if not submit_button:
            # Si aucun bouton n'est trouvé avec les sélecteurs, essayer avec le texte du bouton
            try:
                # Recherche par texte (moins fiable mais solution de secours)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    text = button.text or ""
                    btn_class = button.get_attribute("class") or ""
                    if "parti" in text or "search" in text.lower() or "submit" in btn_class.lower():
                        submit_button = button
                        logger.info(f"Bouton de soumission trouvé avec le texte: {button.text}")
                        break
            except Exception as e:
                logger.warning(f"Tentative de recherche par texte échouée: {e}")
                
        if submit_button:
            # Essayer trois méthodes de clic différentes en séquence
            click_methods = [
                ("JavaScript", lambda btn: driver.execute_script("arguments[0].click();", btn)),
                ("ActionChains", lambda btn: ActionChains(driver).move_to_element(btn).click().perform()),
                ("Native", lambda btn: btn.click())
            ]
            
            click_success = False
            for method_name, click_method in click_methods:
                try:
                    logger.info(f"Tentative de clic par {method_name}...")
                    click_method(submit_button)
                    logger.info(f"Clic par {method_name} réussi")
                    click_success = True
                    break
                except Exception as e:
                    logger.warning(f"Clic par {method_name} a échoué: {e}")
            
            if not click_success:
                logger.error("Toutes les méthodes de clic ont échoué")
                raise Exception("Impossible de cliquer sur le bouton de soumission")
            
            logger.info("Formulaire soumis, attente des résultats...")
            
            # Retour au contenu principal
            driver.switch_to.default_content()
            
            # Attendre que la page change (URL ou contenu)
            start_url = driver.current_url
            start_time = time.time()
            wait_time = 15  # Temps d'attente maximum
            
            # Boucle d'attente avec vérification d'URL ou contenu changé
            while time.time() - start_time < wait_time:
                    if driver.current_url != start_url:
                        logger.info("URL changée - transition de page détectée")
                        break
                        
                    # Vérifier si des éléments de résultats sont présents
                    try:
                        # Vérifier si on a été redirigé vers "La bonne alternance"
                        if "labonnealternance" in driver.current_url:
                            logger.info(f"Redirection vers La bonne alternance détectée: {driver.current_url}")
                            break
                            
                        # Vérifier si une iframe La bonne alternance est présente
                        iframes = driver.find_elements(By.TAG_NAME, "iframe")
                        for iframe in iframes:
                            src = iframe.get_attribute("src")
                            if src and "labonnealternance" in src:
                                logger.info(f"Iframe La bonne alternance détectée: {iframe.get_attribute('src')}")
                                break
                        
                        # Vérifier les éléments spécifiques à La bonne alternance
                        if driver.find_elements(By.CSS_SELECTOR, ".chakra-container, .chakra-heading, [data-testid], .desktop-widget"):
                            logger.info("Éléments de La bonne alternance détectés")
                            break
                            
                        # Anciens sélecteurs pour compatibilité
                        if driver.find_elements(By.CSS_SELECTOR, "#result-list-content, .fr-card, .result-item"):
                            logger.info("Éléments de résultats standards détectés")
                            break
                    except Exception as e:
                        logger.debug(f"Exception lors de la vérification des résultats: {e}")
                        pass
                        
                    time.sleep(0.5)
            
            # Pause supplémentaire pour s'assurer que tout est chargé
            logger.info("Attente supplémentaire pour finaliser le chargement...")
            time.sleep(5)
        else:
            logger.error("Impossible de trouver le bouton de soumission")
            raise Exception("Bouton de soumission non trouvé")
        
        logger.info("Formulaire soumis. Attente des résultats...")
        
        # Retour au contexte principal et attente des résultats
        logger.info("Retour au contexte principal de la page.")
        driver.switch_to.default_content()
        
        # Attendre soit un changement d'URL, soit l'apparition des résultats
        current_url = driver.current_url
        
        # Définir un timeout plus long pour l'attente des résultats
        wait_results = WebDriverWait(driver, 20)  # 20 secondes de timeout
        
        try:
            # Attendre que soit l'URL change, soit le conteneur de résultats apparaît
            logger.info("Attente de chargement des résultats...")
            result_container = wait_results.until(
                lambda d: (d.current_url != current_url) or 
                          ("labonnealternance" in d.current_url) or
                          any("labonnealternance" in iframe.get_attribute("src") 
                              for iframe in d.find_elements(By.TAG_NAME, "iframe")) or
                          d.find_elements(By.CSS_SELECTOR, ".chakra-container, .chakra-heading, [data-testid], .desktop-widget") or
                          d.find_elements(By.ID, "result-list-content")
            )
            
            # Identifier le type de page de résultats
            is_bonne_alternance = "labonnealternance" in driver.current_url
            has_bonne_alternance_iframe = any("labonnealternance" in iframe.get_attribute("src") 
                                              for iframe in driver.find_elements(By.TAG_NAME, "iframe"))
            
            if is_bonne_alternance or has_bonne_alternance_iframe:
                logger.info(f"Page 'La bonne alternance' chargée. URL finale: {driver.current_url}")
            else:
                logger.info(f"Page de résultats standard chargée. URL finale: {driver.current_url}")
            time.sleep(2)  # Pause pour s'assurer que le JavaScript a terminé le rendu
        except TimeoutException:
            logger.error("Timeout: la page de résultats n'a pas chargé dans le délai imparti.")
            # Sauvegarder la page pour diagnostic
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"debug_screenshots/timeout_results_{timestamp}.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                logger.info(f"Capture d'écran de diagnostic enregistrée dans {screenshot_path}")
                
                # Sauvegarder également le code source de la page
                source_path = f"debug_screenshots/page_source_{timestamp}.html"
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                logger.info(f"Code source de la page enregistré dans {source_path}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde du diagnostic: {e}")
                
            # Vérifier si nous avons une iframe labonnealternance et l'afficher dans les logs
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    src = iframe.get_attribute("src")
                    if src and "labonnealternance" in src:
                        logger.info(f"Iframe labonnealternance détectée mais non traitée: {src}")
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des iframes: {e}")
            with open('page_apres_soumission_erreur.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("État de la page sauvegardé dans 'page_apres_soumission_erreur.html'")
        except Exception as e:
            logger.error(f"Erreur lors de la tentative de soumission du formulaire: {e}")
            # Sauvegarder la page pour diagnostic
            with open('page_erreur_soumission.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("État de la page sauvegardé dans 'page_erreur_soumission.html'")

        try:
            # Petite pause pour s'assurer que le JS a fini de rendre les éléments
            time.sleep(3)

        except TimeoutException:
            logger.error("Le conteneur des résultats (id='result-list-content') n'est pas apparu après la soumission.")
            logger.info("Sauvegarde de la page actuelle pour débogage...")
            error_page_path = os.path.join(os.path.dirname(__file__), 'page_apres_soumission_erreur.html')
            with open(error_page_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Page sauvegardée dans : {error_page_path}")
            raise # Re-raise the exception to stop the script
        
        # Sauvegarde du code source de la page de résultats pour analyse...
        logger.info("Sauvegarde du code source de la page de résultats pour analyse...")
        results_filepath = os.path.join(os.path.dirname(__file__), 'page_resultats.html')
        with open(results_filepath, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"✅ Code source des résultats sauvegardé dans '{results_filepath}'.")
        
        # Traitement spécifique pour La bonne alternance
        job_offers = []
        
        # Vérifier si nous avons une iframe de La bonne alternance
        labonne_iframe = None
        try:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src")
                if src and "labonnealternance" in src:
                    labonne_iframe = iframe
                    logger.info(f"Iframe La bonne alternance trouvée pour extraction: {src}")
                    break
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de l'iframe: {e}")
        
        if labonne_iframe:
            # Traitement spécifique pour La bonne alternance
            try:
                # Initialiser la liste des offres
                job_offers = []
                
                # Basculer vers l'iframe
                logger.info("Basculement vers l'iframe La bonne alternance...")
                driver.switch_to.frame(labonne_iframe)
                print("=== PAUSE POUR INSPECTION MANUELLE : 120 secondes ===")
                time.sleep(7)
                
                # Attendre que le contenu de l'iframe se charge complètement
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-card, div[role='group'], .chakra-stack")))
                    logger.info("Contenu de l'iframe chargé avec succès")
                    try:
                        formations_checkbox = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='checkbox'][name='formations']"))
                        )
                        if formations_checkbox.is_selected():
                            driver.execute_script("arguments[0].click();", formations_checkbox)
                            logger.info("Case 'Formations' décochée dans la zone de filtres après la recherche.")
                        else:
                            logger.info("Case 'Formations' déjà décochée dans la zone de filtres.")
                    except Exception as e:
                        logger.warning(f"Impossible de décocher la case 'Formations' dans la zone de filtres : {e}")
                except TimeoutException:
                    logger.warning("Timeout en attendant le chargement du contenu de l'iframe - continuons quand même")
                
                # Capturer une capture d'écran pour le debug
                screenshot_path = "debug_screenshots/labonnealternance_content.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                driver.save_screenshot(screenshot_path)
                logger.info(f"Capture d'écran de l'iframe enregistrée dans {screenshot_path}")
                
                # Afficher l'HTML complet de l'iframe pour debug
                iframe_html = driver.page_source
                debug_html_path = "debug_screenshots/labonnealternance_html.html"
                os.makedirs(os.path.dirname(debug_html_path), exist_ok=True)
                with open(debug_html_path, 'w', encoding='utf-8') as f:
                    f.write(iframe_html)
                logger.info(f"HTML de l'iframe sauvegardé dans {debug_html_path}")
                
                # Scroll pour charger plus de contenu si nécessaire (important pour le chargement dynamique)
                try:
                    for _ in range(3):  # Scrollez 3 fois pour charger plus de contenu
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"Erreur lors du scroll: {e} - continuons quand même")
                
                # Différentes stratégies de sélection des offres
                selectors_strategies = [
                    ".fr-card",  # Format standard France Connect
                    "div[role='group']",  # Chakra UI groupes (structure commune)
                    ".chakra-stack .chakra-card",  # Format Chakra UI card
                    ".chakra-stack > div:not([class])",  # Divs directs dans les stacks (souvent utilisé pour les cartes)
                    ".chakra-box div[role='group']", # Boîtes Chakra contenant des groupes
                    ".result-item, .fr-tile, .tile" # Classes communes pour les résultats de recherche
                ]
                
                # Essayer chaque stratégie de sélecteur jusqu'à trouver des résultats
                formation_cards = []
                for selector in selectors_strategies:
                    logger.info(f"Essai avec le sélecteur: {selector}")
                    formation_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if formation_cards:
                        logger.info(f"Trouvé {len(formation_cards)} éléments avec le sélecteur {selector}")
                        break
                
                if not formation_cards:
                    # Dernier recours: chercher tous les conteneurs qui pourraient être des cartes
                    logger.warning("Aucune offre trouvée avec les sélecteurs standards. Essai avec sélecteur générique...")
                    formation_cards = driver.find_elements(By.CSS_SELECTOR, ".chakra-box, div[role], article, section > div")
                    logger.info(f"Tentative de secours: {len(formation_cards)} éléments potentiels trouvés")
                
                # Pas de limite fixe pour le nombre d'offres, mais filtrons les cartes trop petites
                valid_cards = []
                for card in formation_cards:
                    # Vérifier si la carte a une taille minimale et du contenu
                    try:
                        if len(card.text.strip()) > 20:  # Au moins 20 caractères de texte
                            valid_cards.append(card)
                    except:
                        continue
                
                logger.info(f"Nombre total de cartes valides: {len(valid_cards)}")
                # AJOUT : Log explicite du nombre total d'offres détectées (hors formations)
                logger.info(f"=== NOMBRE TOTAL D'OFFRES DÉTECTÉES (hors formations) : {len(valid_cards)} ===")
                
                # Récupérer les URL de base pour les liens relatifs
                base_url = "https://labonnealternance.apprentissage.beta.gouv.fr"
                
                # Filtrer les cartes pour ignorer les formations
                filtered_cards = []
                for card in valid_cards:
                    try:
                        tag = card.find_element(By.CSS_SELECTOR, ".chakra-text.mui-ulcbns").text.strip()
                        if tag.upper() == "FORMATION":
                            continue  # ignorer les formations
                        filtered_cards.append(card)
                    except Exception:
                        # Si le tag n'existe pas, c'est peut-être une offre d'emploi
                        filtered_cards.append(card)

                logger.info(f"Nombre de cartes après filtrage des formations: {len(filtered_cards)}")
                
                # Extraire les informations de chaque carte d'offre/formation
                for index, card in enumerate(filtered_cards):
                    logger.info(index, card.get_attribute('outerHTML'))
                    try:
                        # Capturer le HTML complet de la carte pour le debug
                        card_html = card.get_attribute('outerHTML')
                        card_debug_path = f"debug_screenshots/card_{index}.html"
                        with open(card_debug_path, 'w', encoding='utf-8') as f:
                            f.write(card_html)
                        
                        # Extraction du titre avec plusieurs stratégies
                        title = "Titre non disponible"
                        title_selectors = [
                            "h3, h4, h5, .chakra-heading, .fr-card__title",  # En-têtes standard
                            "[data-testid*='title'], [class*='title'], strong, b",  # Attributs data ou classes contenant 'title'
                            ".chakra-text:first-of-type, p:first-of-type"  # Premier élément de texte
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_element = card.find_element(By.CSS_SELECTOR, selector)
                                title_text = title_element.text.strip()
                                if title_text and len(title_text) > 3:  # Au moins 3 caractères
                                    title = title_text
                                    break
                            except:
                                continue
                        
                        if title == "Titre non disponible":
                            # Fallback: utiliser la première ligne du texte de la carte
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            if text_lines:
                                title = text_lines[0]
                        
                        # Extraction de l'entreprise/établissement
                        company = "Entreprise non disponible"
                        company_selectors = [
                            ".fr-card__desc, .chakra-text[data-testid*='company']",
                            "p:not(:first-child), .subtitle, [class*='company']",
                            ".chakra-stack p"  # Paragraphes dans un chakra-stack
                        ]
                        
                        for selector in company_selectors:
                            try:
                                company_elements = card.find_elements(By.CSS_SELECTOR, selector)
                                if company_elements:
                                    for elem in company_elements:
                                        text = elem.text.strip()
                                        if text and not any(x in text.lower() for x in ["date", "durée", "km", "à "]) and len(text) > 3:
                                            company = text
                                            break
                            except:
                                continue
                        
                        if company == "Entreprise non disponible":
                            # Fallback: chercher la deuxième ligne de texte ou une ligne qui semble être un nom d'entreprise
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            if len(text_lines) > 1:
                                company = text_lines[1]
                        
                        # Extraction du lieu avec recherche de code postal ou ville
                        location = "Lieu non disponible"
                        location_selectors = [
                            ".fr-card__start, address, [data-testid*='location'], [class*='location']",
                            ".chakra-text:contains('km'), .chakra-text:contains('Paris'), .chakra-text:contains('Lyon')",
                            "span:contains('km'), div:contains('km')",
                            "p:contains(', ')"  # Format commun pour les adresses: "Ville, Code postal"
                        ]
                        
                        
                        postal_code_pattern = re.compile(r'\b\d{5}\b')  # Regex pour les codes postaux français
                        
                        for selector in location_selectors:
                            try:
                                location_elements = card.find_elements(By.CSS_SELECTOR, selector.replace(':contains', ''))
                                if location_elements:
                                    for elem in location_elements:
                                        text = elem.text.strip()
                                        # Si le texte contient un code postal ou une distance en km, c'est probablement un lieu
                                        if text and (postal_code_pattern.search(text) or 'km' in text.lower() or any(city in text for city in ['Paris', 'Lyon', 'Marseille', 'Toulouse'])):
                                            location = text
                                            break
                            except:
                                continue
                        
                        if location == "Lieu non disponible":
                            # Fallback: chercher une ligne contenant un code postal ou km
                            text_lines = [line.strip() for line in card.text.split('\n') if line.strip()]
                            for line in text_lines:
                                if postal_code_pattern.search(line) or 'km' in line.lower():
                                    location = line
                                    break
                        
                        # Tenter d'extraire un lien
                        link = ""
                        try:
                            link_element = card.find_element(By.TAG_NAME, "a")
                            link = link_element.get_attribute('href') or ""
                            if link and link.startswith('/'):
                                link = f"{base_url}{link}"
                        except:
                            link = ""
                        
                        # Déterminer le type d'offre
                        card_text = card.text.lower()
                        offer_type = "Indéterminé"  # Par défaut
                        
                        # Capture d'une capture d'écran de la carte pour analyse
                        try:
                            driver.execute_script("arguments[0].style.border = '3px solid red';", card)
                            driver.save_screenshot(f'debug_screenshots/card_analyzed_{index}.png')
                            driver.execute_script("arguments[0].style.border = '';", card)
                        except:
                            pass
                            
                        # Recherche de mots-clés forts dans le titre et la description pour les formations
                        formation_keywords_strong = [
                            "formation", "bts", "bachelor", "master", "licence", "dut", 
                            "certifica", "certificat", "diplôme", "rncp", 
                            "(bts)", "(master)", "(bachelor)", "(licence)", "(dut)", "(mba)", 
                            "(tp)", "(lp)", "(formatives)", "formation en"
                        ]
                        
                        # Mots-clés secondaires pour les formations
                        formation_keywords_weak = [
                            "école", "étude", "deust", "formatives", "cfa", "institut", 
                            "eemi", "formasup", "université", "centre", "cnam", "formation 100%", 
                            "distanc", "parcours", "étudiant", "apprentissage", "bac", "bac+"
                        ]
                        
                        # Identifiants forts pour les offres d'emploi
                        entreprise_keywords_strong = [
                            "métier", "entreprise recrute", "poste", "contrat", 
                            "cdi", "cdd", "emploi", "offre d'emploi", "job", 
                            "recrut", "recherche un", "recherche une", "embauche", "salaire",
                            "rémunération", "expérience", "temps plein", "temps partiel"
                        ]
                        
                        # Mots-clés secondaires pour les offres d'emploi
                        entreprise_keywords_weak = [
                            "entreprise", "alternance", "commercial", "vendeur", "acheteur", 
                            "manager", "directeur", "assistant", "technicien", "ingénieur",
                            "responsable", "chef", "chargé", "collaborateur", "candidature"
                        ]
                        
                        # Règles de détection plus précises avec pondération avancée
                        formation_score = 0
                        entreprise_score = 0
                        
                        # Créer un dictionnaire des détails de scoring pour le débogage
                        score_details = {
                            "formation_matches": {},
                            "entreprise_matches": {}
                        }
                        
                        # Vérifier si les mots "MÉTIER" ou "FORMATION" apparaissent explicitement
                        # Ce sont des marqueurs très forts utilisés par le site
                        if "MÉTIER" in card.text or "métier" in card_text:
                            entreprise_score += 15  # Pondération encore plus forte - indicateur crucial
                            score_details["entreprise_matches"]["MÉTIER (marqueur explicite)"] = 15
                        
                        if "FORMATION" in card.text or "(formation)" in card_text:
                            formation_score += 15  # Pondération encore plus forte - indicateur crucial
                            score_details["formation_matches"]["FORMATION (marqueur explicite)"] = 15
                            
                        # 1. Vérifier les mots-clés forts pour les formations avec pondération élevée
                        for term in formation_keywords_strong:
                            if term in card_text:
                                formation_score += 3  # Pondération forte (3x)
                                score_details["formation_matches"][f"strong: {term}"] = 3
                                
                        # 2. Vérifier les mots-clés secondaires pour les formations
                        for term in formation_keywords_weak:
                            if term in card_text:
                                formation_score += 1  # Pondération standard
                                score_details["formation_matches"][f"weak: {term}"] = 1
                                
                        # 3. Vérifier les mots-clés forts pour les offres d'emploi
                        for term in entreprise_keywords_strong:
                            if term in card_text:
                                entreprise_score += 4  # Pondération très forte (4x) pour compenser le biais
                                score_details["entreprise_matches"][f"strong: {term}"] = 4
                                
                        # 4. Vérifier les mots-clés secondaires pour les offres d'emploi
                        for term in entreprise_keywords_weak:
                            if term in card_text:
                                entreprise_score += 2  # Pondération forte (2x)
                                score_details["entreprise_matches"][f"weak: {term}"] = 2
                        
                        # 5. Détecter les titres d'offres
                        card_lines = card.text.split('\n')
                        if len(card_lines) > 1:
                            first_line = card_lines[0].strip()
                            # Format typique d'une formation: BTS COMMERCE INTERNATIONAL (titre en majuscules)
                            if first_line.isupper() and len(first_line) > 5:
                                # Vérifier les acronymes courants de formation en majuscules
                                if any(kw in first_line for kw in ["BTS", "MASTER", "LICENCE", "BACHELOR", "CAP", "MBA", "DUT"]):
                                    formation_score += 8  # Très forte indication d'une formation
                                    score_details["formation_matches"]["Titre en majuscules avec acronyme de formation"] = 8
                            
                            # Format typique d'un intitulé de poste: Commercial, Assistant, etc.
                            if not first_line.isupper() and len(first_line) > 5:
                                # Vérifier les termes courants des offres d'emploi
                                if any(kw in first_line.lower() for kw in ["recrute", "recherche", "cdi", "cdd", "poste"]):
                                    entreprise_score += 7  # Forte indication d'un poste
                                    score_details["entreprise_matches"]["Titre avec termes d'emploi"] = 7
                        
                        # 6. Analyse spécifique pour La Bonne Alternance
                        # Sur ce site, les offres de formations contiennent souvent des parenthèses avec le type
                        if any(pattern in card_text for pattern in ["(bts)", "(bachelor)", "(master)", "(licence)", "(mba)", "(dut)", "(formatives)", "(tp)", "(lp)"]):
                            formation_score += 10  # Indication très forte d'une formation
                            score_details["formation_matches"]["Format avec parenthèses typiques des formations"] = 10
                            
                        # 7. Vérification de l'URL si disponible
                        if link and "/offres/" in link.lower():
                            entreprise_score += 6  # Les URLs des offres d'emploi contiennent souvent "/offres/"
                            score_details["entreprise_matches"]["URL contenant /offres/"] = 6
                        elif link and "/formations/" in link.lower():
                            formation_score += 6  # Les URLs des formations contiennent souvent "/formations/"
                            score_details["formation_matches"]["URL contenant /formations/"] = 6
                            
                        # Décision finale basée sur les scores avec une analyse plus raffinée
                        if formation_score > entreprise_score * 1.2:  # Exige une différence significative pour être classé comme formation
                            offer_type = "Formation"
                            decision_reason = "Score formation significativement plus élevé"
                        elif entreprise_score > formation_score * 1.0:  # Moins strict pour les offres d'emploi
                            offer_type = "Entreprise"
                            decision_reason = "Score entreprise plus élevé"
                        else:
                            # En cas de scores proches, utiliser des critères de décision supplémentaires
                            
                            # Vérifier des marqueurs explicites très spécifiques
                            if any(marker in card.text for marker in ["UNIVERSIT", "FORMATION", "BTS ", " BTS", "LICENCE", "BACHELOR"]):
                                offer_type = "Formation" 
                                decision_reason = "Marqueurs explicites de formation détectés dans un cas ambigu"
                            elif "MÉTIER" in card.text or any(marker in card_text for marker in ["cdi", "cdd", "recrute", "poste de"]):
                                offer_type = "Entreprise"
                                decision_reason = "Marqueurs explicites d'emploi détectés dans un cas ambigu"
                            else:
                                # Dans le doute absolu, préférer les offres d'emploi comme demandé par l'utilisateur
                                offer_type = "Entreprise"
                                decision_reason = "Décision par défaut - favorise les offres d'entreprise"
                            
                        # Log détaillé pour le débogage
                        log_detail = f"Carte analysée:\n"
                        log_detail += f"- Titre: {title[:50]}...\n"
                        log_detail += f"- Score formation: {formation_score}, détails: {score_details['formation_matches']}\n"
                        log_detail += f"- Score entreprise: {entreprise_score}, détails: {score_details['entreprise_matches']}\n"
                        log_detail += f"- Type final: {offer_type} (Raison: {decision_reason})\n"
                        logger.info(log_detail)
                        
                        # Filtrer uniquement les offres qui ne sont pas des formations
                        if offer_type == "Formation":
                            # Enregistrer le détail de la formation ignorée pour débogage
                            text_clean = card.text.replace('\n', ' ')
                            logger.info(f"Formation ignorée: {text_clean[:100]}")
                            continue
                        
                        # Créer un dictionnaire avec les informations de l'offre
                        job_offer = {
                            "title": title,
                            "company": company,
                            "location": location,
                            "link": link,
                            "type": offer_type,
                            "source": "La bonne alternance",
                            "postulation_status": "non_postulé"  # Statut initial
                        }
                        
                        # --- Bloc de postulation automatique robuste pour La Bonne Alternance ---
                        if link and AUTO_POSTULER:
                            logger.info(f"Tentative de postulation automatique pour: {title} chez {company}")
                            current_url = driver.current_url
                            current_handles = driver.window_handles
                            main_handle = driver.current_window_handle
                            driver.execute_script("window.open(arguments[0], '_blank');", link)
                            time.sleep(2)
                            new_handles = [handle for handle in driver.window_handles if handle != main_handle]
                            if new_handles:
                                driver.switch_to.window(new_handles[0])
                                # Vérifier si l'offre redirige vers un site externe (HelloWork, Meteojob, etc.)
                                external_domains = ["hellowork.com", "meteojob.com", "jobteaser.com", "apec.fr"]
                                current_url = driver.current_url
                                if any(domain in current_url for domain in external_domains):
                                    logger.info(f"Redirection externe détectée ({current_url}), on passe à l'offre suivante via le bouton 'next'.")
                                    if driver.current_window_handle != main_handle:
                                        driver.close()
                                        driver.switch_to.window(main_handle)
                                    try:
                                        next_btn = driver.find_element(By.CSS_SELECTOR, "button[data-testid='next-button']")
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                                        time.sleep(0.5)
                                        next_btn.click()
                                        logger.info("Bouton 'next' cliqué pour passer à l'offre suivante.")
                                        time.sleep(2)
                                    except Exception as e:
                                        logger.warning(f"Impossible de cliquer sur le bouton 'next' : {e}")
                                    continue
                                try:
                                    wait = WebDriverWait(driver, 20)
                                    # 1. Clic sur le premier bouton "J'envoie ma candidature"
                                    logger.info("Recherche du bouton 'J'envoie ma candidature' (postuler-button)...")
                                    postuler_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-testid="CandidatureSpontanee"] button[data-testid="postuler-button"]')))
                                    postuler_btn.click()
                                    logger.info("Bouton 'J'envoie ma candidature' cliqué.")
                                    # 2. Attendre l'apparition du formulaire modal
                                    logger.info("Attente de l'apparition du formulaire modal...")
                                    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'section.chakra-modal__content[role="dialog"] form[data-sentry-component="CandidatureLbaModalBody"]')))
                                    # 3. Remplir les champs obligatoires
                                    logger.info("Remplissage des champs du formulaire...")
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="lastName"]').clear()
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="lastName"]').send_keys("DUPONT")
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="firstName"]').clear()
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="firstName"]').send_keys("Jean")
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="email"]').clear()
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="email"]').send_keys("silasiharis@gmail.com")
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="phone"]').clear()
                                    driver.find_element(By.CSS_SELECTOR, 'input[data-testid="phone"]').send_keys("0601020304")
                                    driver.find_element(By.CSS_SELECTOR, 'textarea[data-testid="message"]').clear()
                                    driver.find_element(By.CSS_SELECTOR, 'textarea[data-testid="message"]').send_keys("Je suis très motivé par cette alternance.")
                                    # 4. Upload du CV (s'assurer que le fichier n'est pas vide !)
                                    cv_path = "/Users/davidravin/Desktop/floup.pdf"  # CV réel de l'utilisateur
                                    if not os.path.exists(cv_path) or os.path.getsize(cv_path) == 0:
                                        logger.error("Le fichier CV est manquant ou vide, annulation de la candidature.")
                                        driver.save_screenshot("debug_screenshots/cv_missing_or_empty.png")
                                        driver.close()
                                        driver.switch_to.window(main_handle)
                                        continue
                                    cv_input = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="fileDropzone"] input[type="file"]')
                                    cv_input.send_keys(cv_path)
                                    logger.info("CV uploadé avec succès.")
                                    time.sleep(2)
                                    # 4.1 Cocher toutes les cases à cocher (checklist anti-bot)
                                    checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                                    for checkbox in checkboxes:
                                        try:
                                            if checkbox.is_displayed() and not checkbox.is_selected():
                                                driver.execute_script("arguments[0].click();", checkbox)
                                                logger.info("Checkbox cochée (anti-bot)")
                                        except Exception as e:
                                            logger.warning(f"Impossible de cocher une checkbox: {e}")
                                    # 5. Clic sur le bouton final d'envoi
                                    logger.info("Recherche du bouton final 'J'envoie ma candidature' (candidature-not-sent)...")
                                    final_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="candidature-not-sent"][type="submit"]')))
                                    time.sleep(7)
                                    final_btn.click()
                                    logger.info("Candidature envoyée avec succès.")
                                      # Pause pour laisser le site traiter la soumission
                                    time.sleep(15)
                                    driver.close()
                                    driver.switch_to.window(main_handle)
                                except Exception as e:
                                    logger.error(f"Erreur lors de la postulation automatique : {e}")
                                
                                    
                            switch_to_iframe_if_needed(driver)
                        
                        job_offers.append(job_offer)
                        logger.info(f"Offre {index+1} ajoutée: {title} chez {company} à {location} ({offer_type}) - Statut postulation: {job_offer['postulation_status']}")
                        
                    except Exception as e:
                        logger.error(f"Erreur lors de l'extraction des données de la carte {index}: {e}", exc_info=True)
                
                # Revenir au contexte principal
                driver.switch_to.default_content()
                logger.info("Retour au contexte principal après traitement de l'iframe")
                
                # Afficher le résumé des offres trouvées
                logger.info(f"Total des offres extraites depuis La bonne alternance: {len(job_offers)}")
                
                # Si des offres ont été trouvées, les retourner directement
                if job_offers:
                    return job_offers
                    
            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'iframe La bonne alternance: {e}")
                driver.switch_to.default_content()  # S'assurer de revenir au contexte principal

        # Si on n'a pas pu extraire depuis l'iframe, essayer la méthode classique
        logger.info("Analyse des résultats via la méthode classique...")
        return parse_results(driver.page_source)

    except Exception as e:
        logger.error(f"Une erreur est survenue dans run_scraper: {e}", exc_info=True)
        if driver:
            timestamp = int(time.time())
            driver.save_screenshot(f'error_screenshot_{timestamp}.png')
            with open(f'error_page_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Screenshot et source de la page sauvegardés.")
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver fermé.")

def parse_results(html_content):
    """Parse la page de résultats pour en extraire les offres."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Le conteneur principal des résultats
        results_container = soup.find('div', id='result-list-content')
        
        if not results_container:
            logger.error("Impossible de trouver le conteneur des offres sur la page (id='result-list-content').")
            # Fallback attempt on the whole body if the specific container is not found
            results_container = soup.find('body')
            if not results_container:
                logger.error("Le corps du document est vide. Impossible de continuer.")
                return
            logger.warning("Conteneur 'result-list-content' non trouvé, recherche des cartes sur toute la page.")

        # Les offres sont des div avec la classe 'fr-card'
        job_offers = results_container.find_all('div', class_='fr-card')
        
        if not job_offers:
            logger.warning("Aucune offre d'emploi trouvée avec le sélecteur 'div.fr-card'. Le site a peut-être changé ou il n'y a pas de résultats pour cette recherche.")
            return

        logger.info(f"{len(job_offers)} offres trouvées. Début de l'extraction...")
        base_url = "https://www.alternance.emploi.gouv.fr"
        extracted_count = 0

        for offer in job_offers:
            title_element = offer.find(['h3', 'h4'], class_='fr-card__title')
            title = title_element.get_text(strip=True) if title_element else 'N/A'
            
            company_element = offer.find('p', class_='fr-card__detail')
            company = company_element.get_text(strip=True) if company_element else 'N/A'

            location_element = offer.find('p', class_='fr-card__start')
            location = location_element.get_text(strip=True) if location_element else 'N/A'
            
            link_element = offer.find('a', class_='fr-card__link')
            link = link_element['href'] if link_element and link_element.has_attr('href') else 'N/A'

            # If any of the main fields are missing, this is likely not a job card we want.
            if title == 'N/A' or company == 'N/A':
                continue
            
            # Make sure the link is absolute
            if link.startswith('/'):
                link = f"{base_url}{link}"
            
            extracted_count += 1
            logger.info("--- Offre --- ")
            logger.info(f"Titre: {title}")
            logger.info(f"Entreprise: {company}")
            logger.info(f"Lieu: {location}")
            logger.info(f"Lien: {link}")
        
        if extracted_count == 0:
            logger.warning("Aucune offre valide n'a pu être extraite des cartes trouvées.")

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse des résultats: {e}", exc_info=True)

def main():
    user_email = 'test@gmail.com' # Email par défaut pour le test
    if len(sys.argv) > 1 and sys.argv[1] != 'test@gmail.com':
        user_email = sys.argv[1]
    
    logger.info(f"Recherche de l'utilisateur : {user_email}")
    # Suppression de la base de données, on utilise directement les données de test
    user_data = {'email': user_email, 'search_query': 'Commercial', 'location': 'Lyon'}

    if user_data:
        run_scraper(user_data)
    else:
        logger.error(f"Aucune donnée utilisateur disponible pour lancer le scraper.")

def setup_and_run():
    """Fonction principale pour configurer les paramètres et lancer le scraper"""
   
    
    # Variables globales à modifier
    global AUTO_POSTULER, PAUSE_APRES_POSTULATION
    
    # Configuration des options en ligne de commande
    parser = argparse.ArgumentParser(description="Scraper pour La Bonne Alternance avec postulation automatique")
    
    # Options pour l'utilisateur
    parser.add_argument("--email", type=str, help="Email de l'utilisateur pour récupérer les données de profil")
    parser.add_argument("--metier", type=str, help="Métier à rechercher (ex: 'Commercial')")
    parser.add_argument("--ville", type=str, help="Ville ou localisation (ex: 'Paris')")
    
    # Options pour la postulation
    parser.add_argument("--postuler", action="store_true", help="Activer la postulation automatique")
    parser.add_argument("--no-postuler", dest="postuler", action="store_false", help="Désactiver la postulation automatique")
    parser.add_argument("--remplir", action="store_true", help="Remplir automatiquement le formulaire de candidature")
    parser.add_argument("--no-remplir", dest="remplir", action="store_false", help="Désactiver le remplissage automatique")
    parser.add_argument("--envoyer", action="store_true", help="Envoyer automatiquement la candidature après remplissage")
    parser.add_argument("--pause", action="store_true", help="Mettre en pause après l'ouverture du formulaire pour inspection manuelle")
    parser.add_argument("--cv", type=str, help="Chemin vers le fichier CV (PDF ou DOCX)")
    
    # Options pour le débogage
    parser.add_argument("--debug", action="store_true", help="Activer le mode débogage avec plus de logs")
    parser.add_argument("--headless", action="store_true", help="Exécuter en mode headless (sans interface graphique)")
    
    # Paramètres par défaut
    parser.set_defaults(
        postuler=AUTO_POSTULER,
        remplir=True if POSTULER_FUNCTIONS_LOADED else False,
        envoyer=False,
        pause=PAUSE_APRES_POSTULATION,
        debug=False,
        headless=False
    )
    
    # Analyser les arguments
    args = parser.parse_args()
    
    # Configurer le mode de débogage si demandé
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Mode debug activé")
    
    # Modifier les variables globales en fonction des arguments
    AUTO_POSTULER = args.postuler
    PAUSE_APRES_POSTULATION = args.pause
    
    # Configurer les variables du module externe si disponible
    if POSTULER_FUNCTIONS_LOADED:
        import postuler_functions_1751543385370 as postuler_functions
        postuler_functions.AUTO_REMPLIR_FORMULAIRE = args.remplir
        postuler_functions.AUTO_ENVOYER_CANDIDATURE = args.envoyer
        if args.cv:
            postuler_functions.CHEMIN_CV = os.path.expanduser(args.cv)
    
    # Afficher la configuration
    logger.info(f"Configuration: Postulation automatique = {AUTO_POSTULER}, "
              f"Remplissage auto = {args.remplir}, "
              f"Envoi auto = {args.envoyer}, "
              f"Pause inspection = {PAUSE_APRES_POSTULATION}")
    
    # Créer un objet user_data à partir des arguments de ligne de commande
    if args.email or args.metier or args.ville:
        user_data = {}
        if args.email:
            user_data['email'] = args.email
        else:
            user_data['email'] = 'test@gmail.com'
            
        if args.metier:
            user_data['search_query'] = args.metier
        
        if args.ville:
            user_data['location'] = args.ville
        
        # Lancer directement le scraper avec les données spécifiées
        run_scraper(user_data)
    else:
        # Lancer le processus normal via la fonction main
        main()

if __name__ == "__main__":
    setup_and_run()
import os
import time
import logging
import traceback
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Configuration du logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Configuration du fichier log persistant
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"postulation_{time.strftime('%Y%m%d_%H%M%S')}.log")
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    # Handler pour le fichier log
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.setLevel(logging.INFO)

# Configuration pour la postulation automatique
AUTO_REMPLIR_FORMULAIRE = True  # Activer/désactiver le remplissage automatique du formulaire
AUTO_ENVOYER_CANDIDATURE = True  # Activer par défaut l'envoi automatique du formulaire après remplissage
PAUSE_AVANT_ENVOI = False  # Désactiver la pause avant l'envoi final pour une automatisation complète

# Assurer l'existence du répertoire pour les captures d'écran de debug
os.makedirs("debug_screenshots", exist_ok=True)

# Message de candidature par défaut
MESSAGE_CANDIDATURE = """Bonjour,

Je suis vivement intéressé(e) par cette offre d'alternance qui correspond parfaitement à mon projet professionnel. 
Mon profil et ma formation correspondent aux compétences requises pour ce poste.

Je serais ravi(e) de pouvoir échanger avec vous pour vous présenter ma motivation et mes ambitions.

Cordialement,
[Prénom Nom]
"""

def remplir_formulaire_candidature(driver, user_data, titre_offre):
    """
    Remplit automatiquement le formulaire de candidature avec les données utilisateur
    """
    try:
        logger.info("Début du remplissage du formulaire de candidature...")
        wait = WebDriverWait(driver, 20)  # Augmenter le temps d'attente à 20s
        
        # Attendre que le formulaire soit complètement chargé
        logger.info("Attente du chargement complet du formulaire...")
        try:
            # Attendre que le formulaire soit visible et chargé
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form[data-sentry-component='CandidatureLbaModalBody']"))) 
            logger.info("✅ Formulaire détecté et chargé")
        except TimeoutException:
            logger.warning("❌ Délai d'attente dépassé pour le chargement du formulaire")
            driver.save_screenshot(f"debug_screenshots/formulaire_non_charge_{titre_offre.replace(' ', '_')}.png")
        
        # Capturer un screenshot au début du remplissage
        try:
            driver.save_screenshot(f"debug_screenshots/formulaire_avant_remplissage_{titre_offre.replace(' ', '_')}.png")
        except Exception as e:
            logger.debug(f"Impossible de capturer le screenshot avant remplissage: {e}")
        
        # Définir les données utilisateur à remplir
        nom = user_data.get('nom', 'Dupont')
        prenom = user_data.get('prenom', 'Jean')
        email = user_data.get('email', 'jean.dupont@example.com')
        telephone = user_data.get('telephone', '0612345678')
        message = user_data.get('message', MESSAGE_CANDIDATURE.replace('[Prénom Nom]', f"{prenom} {nom}"))
        
        # Mapping des champs avec les sélecteurs exacts du DOM
        fields_mapping = {
            "lastName": {
                "value": nom,
                "selectors": ["input[data-testid='lastName']", "#lastName", "input[name='applicant_last_name']", "//input[@data-testid='lastName']"] 
            },
            "firstName": {
                "value": prenom,
                "selectors": ["input[data-testid='firstName']", "#firstName", "input[name='applicant_first_name']", "//input[@data-testid='firstName']"] 
            },
            "email": {
                "value": email,
                "selectors": ["input[data-testid='email']", "#email", "input[name='applicant_email']", "//input[@data-testid='email']"] 
            },
            "phone": {
                "value": telephone,
                "selectors": ["input[data-testid='phone']", "#phone", "input[name='applicant_phone']", "//input[@data-testid='phone']"] 
            },
            "message": {
                "value": message,
                "selectors": ["textarea[data-testid='message']", "textarea[name='applicant_message']", "#message", "//textarea[@data-testid='message']"] 
            }
        }
        
        # Remplir chaque champ avec plusieurs tentatives de sélecteurs
        for field_name, field_info in fields_mapping.items():
            field_found = False
            value = field_info["value"]
            selectors = field_info["selectors"]
            
            for selector in selectors:
                try:
                    if selector.startswith("//"):  # XPath
                        field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    else:  # CSS
                        field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    
                    # Mettre en évidence le champ pour le débogage
                    driver.execute_script("arguments[0].style.border='3px solid green';", field)
                    
                    # Effacer et remplir le champ
                    field.clear()
                    field.send_keys(value)
                    logger.info(f"✅ Champ {field_name} rempli avec succès")
                    field_found = True
                    break
                except Exception as e:
                    logger.debug(f"Sélecteur {selector} pour {field_name} non trouvé: {str(e)[:100]}...")
                    continue
            
            if not field_found:
                logger.warning(f"⚠️ Impossible de trouver le champ {field_name}")
                # Capture d'écran en cas d'échec
                driver.save_screenshot(f"debug_screenshots/champ_non_trouve_{field_name}_{titre_offre.replace(' ', '_')}.png")
        
        # Gestion des documents (CV et LM) qui sont déjà sur le profil de l'utilisateur
        logger.info("Recherche des champs d'upload de documents...")
        
        # Tableau des types de documents à gérer et leurs sélecteurs potentiels
        document_types = [
            {
                "name": "CV",
                "selectors": [
                    "input[type='file'][accept='.docx,.pdf']", 
                    "input[type='file'][data-testid='cv-upload']",
                    "//input[@type='file' and contains(@accept, '.pdf')]"
                ]
            },
            {
                "name": "Lettre de motivation", 
                "selectors": [
                    "input[type='file'][data-testid='lm-upload']",
                    "input[type='file'][accept='.docx,.pdf']:not(:first-child)",
                    "//input[@type='file'][position()>1]"
                ]
            }
        ]
        
        # Signaler que les documents sont déjà associés au profil utilisateur
        logger.info("✅ Documents utilisateur (CV et LM) déjà associés au profil - ils seront utilisés automatiquement")
        
        # Vérifier si des champs d'upload sont présents et les mettre en évidence pour débogage
        for doc_type in document_types:
            for selector in doc_type["selectors"]:
                try:
                    if selector.startswith("//"): # XPath
                        upload_field = driver.find_element(By.XPATH, selector)
                    else: # CSS
                        upload_field = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Si un champ est trouvé, vérifier s'il est obligatoire ou si le système utilise déjà le document associé au profil
                    if upload_field:
                        is_required = upload_field.get_attribute("required") == "true" or upload_field.get_attribute("aria-required") == "true"
                        logger.info(f"Champ d'upload pour {doc_type['name']} détecté (obligatoire: {is_required})")
                        
                        # Mettre en évidence le champ pour débogage
                        driver.execute_script("arguments[0].style.border='2px dashed blue'; arguments[0].style.backgroundColor='rgba(0,0,255,0.1)'", upload_field)
                        
                        # Vérifier si le système a automatiquement associé le document du profil utilisateur
                        try:
                            confirmation_text = driver.find_element(By.XPATH, f"//div[contains(text(), '{doc_type['name']}') and contains(text(), 'chargé')]")
                            logger.info(f"✅ Confirmation que le {doc_type['name']} du profil utilisateur est bien utilisé")
                        except NoSuchElementException:
                            if is_required:
                                logger.warning(f"⚠️ Le {doc_type['name']} semble obligatoire mais n'est pas automatiquement associé depuis le profil")
                            else:
                                logger.debug(f"Pas de confirmation explicite pour l'utilisation du {doc_type['name']} du profil")
                        break
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.debug(f"Erreur lors de la vérification du champ d'upload pour {doc_type['name']}: {str(e)[:100]}...")
                    continue
        
        # Gestion des cases à cocher (consentement) avec les sélecteurs précis
        checkbox_selectors = [
            ".chakra-checkbox input[type='checkbox']",  # Sélecteur basé sur la structure fournie
            "input.chakra-checkbox__input",  # Classe spécifique
            "input[type='checkbox']",  # Sélecteur générique
            "//label[contains(@class, 'chakra-checkbox')]/input",  # XPath par label parent
        ]
        
        logger.info("Recherche et activation des cases à cocher...")
        checkboxes_found = False
        for selector in checkbox_selectors:
            try:
                if selector.startswith("//"):  # XPath
                    checkboxes = driver.find_elements(By.XPATH, selector)
                else:  # CSS
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if checkboxes:
                    checkboxes_found = True
                    logger.info(f"{len(checkboxes)} cases à cocher trouvées")
                    
                    for i, checkbox in enumerate(checkboxes):
                        try:
                            # Tenter différentes approches pour cocher la case
                            try:
                                # D'abord essayer de cliquer sur le label parent (plus fiable)
                                parent_label = driver.find_element(By.XPATH, f"(//label[contains(@class, 'chakra-checkbox')])[{i+1}]")
                                driver.execute_script("arguments[0].click();", parent_label)
                            except:
                                # Sinon, essayer avec JavaScript directement sur la case
                                driver.execute_script("arguments[0].click();", checkbox)
                            
                            logger.info(f"✅ Case à cocher {i+1} activée")
                            time.sleep(0.5)  # Courte pause entre chaque clic
                        except Exception as checkbox_error:
                            logger.warning(f"⚠️ Erreur lors du clic sur la case {i+1}: {str(checkbox_error)[:100]}...")
                    break
            except Exception as e:
                logger.debug(f"Sélecteur {selector} pour cases à cocher non trouvé: {str(e)[:100]}...")
                
        if not checkboxes_found:
            logger.warning("⚠️ Aucune case à cocher trouvée - possible changement dans la structure du formulaire")
            driver.save_screenshot(f"debug_screenshots/no_checkboxes_{titre_offre.replace(' ', '_')}.png")
        
        # Soumission du formulaire avec les sélecteurs précis pour le bouton final
        try:
            # Sélectionner toutes les cases à cocher
            checkboxes = driver.find_elements(By.CSS_SELECTOR, ".chakra-checkbox__control")
            for checkbox in checkboxes:
                try:
                    # Utiliser JavaScript pour simuler un clic sur la case
                    driver.execute_script("arguments[0].click();", checkbox)
                except:
                    continue
            logger.info("✅ Cases à cocher activées")
        except Exception as e:
            logger.warning(f"Impossible de cocher les cases: {e}")
        
        # Remplir les champs obligatoires
        try:
            # Nom
            nom_field = wait.until(EC.presence_of_element_located((By.ID, "lastName")))
            nom_field.clear()
            nom_field.send_keys(user_data.get('nom', 'Nom'))
            
            # Prénom
            prenom_field = wait.until(EC.presence_of_element_located((By.ID, "firstName")))
            prenom_field.clear()
            prenom_field.send_keys(user_data.get('prenom', 'Prénom'))
            
            # Email
            email_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
            email_field.clear()
            email_field.send_keys(user_data.get('email', 'email@example.com'))
            
            # Téléphone
            phone_field = wait.until(EC.presence_of_element_located((By.ID, "phone")))
            phone_field.clear()
            phone_field.send_keys(user_data.get('telephone', '0612345678'))
            
            logger.info("✅ Champs personnels remplis avec succès")
        except Exception as e:
            logger.warning(f"Erreur lors du remplissage des champs personnels: {e}")
            driver.save_screenshot(f"debug_screenshots/erreur_champs_personnels_{titre_offre.replace(' ', '_')}.png")
        
        # Option pour envoyer automatiquement la candidature
        if AUTO_ENVOYER_CANDIDATURE:
            try:
                # Liste de sélecteurs pour le bouton d'envoi final
                submit_selectors = [
                    "button[type='submit']",
                    ".fr-btn--submit",
                    "button.chakra-button[type='submit']",
                    "//button[contains(., 'J\'envoie ma candidature')]",
                    "//button[contains(., 'Envoyer')]",
                    "//button[contains(., 'Soumettre')]",
                    "//button[@type='submit']"
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        if selector.startswith("/"):
                            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        else:
                            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        if submit_button:
                            break
                    except Exception:
                        continue
                
                if not submit_button:
                    # Tentative de recherche par JavaScript
                    logger.info("⚠️ Tentative de recherche du bouton de soumission par JavaScript...")
                    js = """
                    function findSubmitButton() {
                        // Rechercher tout bouton qui ressemble à un bouton de soumission
                        const buttons = document.querySelectorAll('button');
                        for (const btn of buttons) {
                            if (btn.type === 'submit' || 
                                btn.textContent.toLowerCase().includes('envoie') ||
                                btn.textContent.toLowerCase().includes('soumettre') ||
                                btn.textContent.toLowerCase().includes('envoyer') ||
                                btn.classList.contains('fr-btn--submit')) {
                                return btn;
                            }
                        }
                        return null;
                    }
                    return findSubmitButton();
                    """
                    submit_button = driver.execute_script(js)
                
                if submit_button:
                    logger.info("Soumission du formulaire de candidature...")
                    driver.execute_script("arguments[0].style.border='3px solid red';arguments[0].scrollIntoView();", submit_button)
                    driver.save_screenshot(f"debug_screenshots/avant_soumission_{titre_offre.replace(' ', '_')}.png")
                    
                    # Cliquer sur le bouton
                    submit_button.click()
                    logger.info(f"✅ Clic sur le bouton de soumission effectué")
                    
                    # Attendre une confirmation
                    try:
                        wait.until(lambda driver: EC.presence_of_element_located((By.CSS_SELECTOR, ".fr-alert--success")) or 
                                  EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Candidature envoyée')]")) or
                                  EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Merci')]")))
                        logger.info(f"✅ Confirmation reçue - Candidature envoyée avec succès pour: {titre_offre}")
                    except:
                        logger.info(f"Pas de confirmation explicite, mais la candidature a probablement été envoyée pour: {titre_offre}")
                    
                    return {"status": "soumis"}
                else:
                    logger.warning(f"Impossible de trouver le bouton de soumission pour {titre_offre}")
                    driver.save_screenshot(f"debug_screenshots/bouton_soumission_non_trouve_{titre_offre.replace(' ', '_')}.png")
                    return {"status": "formulaire_rempli", "soumission": "echec", "raison": "bouton_non_trouve"}
                    
            except Exception as e:
                logger.warning(f"Erreur lors de la soumission du formulaire: {e}")
                driver.save_screenshot(f"debug_screenshots/erreur_soumission_{titre_offre.replace(' ', '_')}.png")
                return {"status": "formulaire_rempli", "soumission": "echec", "raison": str(e)}
        else:
            logger.info("Formulaire rempli avec succès, en attente de confirmation manuelle pour l'envoi")
            return {"status": "formulaire_rempli", "soumission": "en_attente"}
            
    except Exception as e:
        logger.error(f"Erreur lors du remplissage du formulaire: {e}")
        driver.save_screenshot(f"debug_screenshots/erreur_remplissage_{titre_offre.replace(' ', '_')}.png")
        return {"status": "echec", "raison": str(e)}

def postuler_offre(driver, url_offre, titre_offre, user_data=None):
    """Ouvre l'offre et postule en remplissant le formulaire"""
    try:
        # Log détaillé
        logger.info(f"=== DÉBUT POSTULATION pour: {titre_offre} - {url_offre} ===") 
        # Ouvrir l'URL dans un nouvel onglet
        driver.execute_script(f"window.open('{url_offre}', '_blank');")
        
        # Basculer vers le nouvel onglet
        driver.switch_to.window(driver.window_handles[-1])
        
        # Attendre que la page soit chargée
        wait = WebDriverWait(driver, 15)
        
        # Vérifier si c'est une candidature spontanée sans contact (impossible de postuler)
        try:
            # Recherche des éléments spécifiques aux candidatures spontanées sans contact
            candidature_spontanee_indicators = [
                "//span[contains(@class, 'chakra-text') and contains(text(), 'CANDIDATURE SPONTANÉE')]",
                "//div[contains(text(), \"Nous n'avons pas de contact pour cette entreprise\")]",
                "//div[@data-sentry-component='NoCandidatureLba']"
            ]
            
            for selector in candidature_spontanee_indicators:
                elements = driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    try:
                        # Prendre une capture d'écran pour debug avec surbrillance
                        driver.execute_script("arguments[0].style.border='3px solid red'", elements[0])
                        screenshot_path = f"debug_screenshots/candidature_spontanee_sans_contact_{titre_offre.replace(' ', '_')}.png"
                        driver.save_screenshot(screenshot_path)
                        
                        logger.warning(f"⚠️ Candidature spontanée sans contact détectée pour '{titre_offre}'. Impossible de postuler automatiquement. Offre ignorée.")
                        logger.info(f"Capture d'écran sauvegardée: {screenshot_path}")
                        
                        # Ignorer cette offre et passer à la suivante
                        return {"status": "ignoré", "raison": "Candidature spontanée sans contact direct"}
                    except Exception as inner_e:
                        logger.debug(f"Erreur lors de la capture d'écran pour candidature spontanée: {str(inner_e)}")
                        return {"status": "ignoré", "raison": "Candidature spontanée sans contact direct (erreur capture)"}
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification de candidature spontanée: {str(e)}")
        
        # Ensuite vérifier s'il y a un bouton ou lien qui redirige vers un site externe
        external_button_selectors = [
            # Sélecteurs spécifiques pour Hellowork basés sur l'exemple reçu
            "//a[@data-tracking-id='postuler-offre-job-partner']",
            "//a[contains(@href, 'holeest.com/redirect')]",
            "//a[contains(@href, 'hellowork.com')]",
            
            # Sélecteurs par texte pour les boutons et liens
            "//button[contains(text(), 'Je postule sur Hellowork')]",
            "//button[contains(., 'Je postule sur Hellowork')]",
            "//a[contains(text(), 'Je postule sur Hellowork')]",
            "//a[contains(., 'Je postule sur Hellowork')]",
            
            # Sélecteurs génériques pour d'autres plateformes externes
            "//button[contains(text(), 'Postuler sur')]",
            "//button[contains(., 'Postuler sur')]",
            "//button[contains(text(), 'Je postule sur')]",
            "//a[contains(text(), 'Je postule sur')]",
            "//a[contains(text(), 'Postuler sur')]"
        ]
        
        # Vérifier si un bouton de redirection externe existe
        for selector in external_button_selectors:
            try:
                external_button = driver.find_element(By.XPATH, selector)
                if external_button:
                    button_text = external_button.text.strip()
                    logger.warning(f"⚠️ Détection d'une redirection externe: '{button_text}' - Offre ignorée")
                    driver.save_screenshot(f"debug_screenshots/redirection_externe_{titre_offre.replace(' ', '_')}.png")
                    return {"status": "ignoré", "raison": f"Redirection vers un site externe: {button_text}"}
            except NoSuchElementException:
                continue
            except Exception as e:
                logger.debug(f"Erreur lors de la recherche des boutons externes: {str(e)[:100]}...")
        
        # Tenter de trouver et cliquer sur le bouton de candidature
        # Multiples sélecteurs pour maximiser les chances
        selectors = [
            "button[data-tracking-id='postuler-offre-lba']",
            "button:contains('J'envoie ma candidature')",
            "//button[contains(., 'J'envoie ma candidature')]",
            ".fr-btn[type='button']",
            "//button[contains(., 'Je candidate')]",
            "//button[contains(., 'Candidater')]",
            "a.fr-btn",
            ".send-application-button"
        ]
        
        bouton_trouve = False
        for selector in selectors:
            try:
                if selector.startswith("//"):  # XPath
                    bouton = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                elif ":contains(" in selector:  # Sélecteur jQuery
                    texte = selector.split(":contains('")[1].split("')")[0]
                    js = f"""
                    var buttons = document.querySelectorAll('button');
                    for (var i = 0; i < buttons.length; i++) {{
                        if (buttons[i].textContent.includes('{texte}')) {{
                            return buttons[i];
                        }}
                    }}
                    return null;
                    """
                    bouton = driver.execute_script(js)
                    
                    # Vérifier que ce n'est pas un bouton vers un site externe
                    if bouton and ("Je postule sur" in bouton.text or "Postuler sur" in bouton.text):
                        logger.warning(f"⚠️ Détection d'une redirection externe: '{bouton.text}' - Offre ignorée")
                        driver.save_screenshot(f"debug_screenshots/redirection_externe_{titre_offre.replace(' ', '_')}.png")
                        return {"status": "ignoré", "raison": f"Redirection vers un site externe: {bouton.text}"}
                    if bouton:
                        wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{texte}')]")))
                else:  # Sélecteur CSS
                    bouton = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                if bouton:
                    # Vérifier si c'est un bouton qui redirige vers un site externe
                    if hasattr(bouton, 'text'):
                        bouton_text = bouton.text.strip()
                        if "Je postule sur" in bouton_text or "Postuler sur" in bouton_text:
                            logger.warning(f"⚠️ Détection d'une redirection externe: '{bouton_text}' - Offre ignorée")
                            driver.save_screenshot(f"debug_screenshots/redirection_externe_{titre_offre.replace(' ', '_')}.png")
                            return {"status": "ignoré", "raison": f"Redirection vers un site externe: {bouton_text}"}
                    
                    logger.info(f"✅ Bouton 'J'envoie ma candidature' trouvé")
                    # Mettre en évidence le bouton pour le débogage
                    driver.execute_script("arguments[0].style.border='3px solid red';", bouton)
                    
                    # Capturer un screenshot avant de cliquer
                    driver.save_screenshot(f"debug_screenshots/avant_clic_candidature_{titre_offre.replace(' ', '_')}.png")
                    
                    # Cliquer sur le bouton
                    bouton.click()
                    logger.info("✅ Premier clic sur le bouton 'J'envoie ma candidature' effectué")
                    bouton_trouve = True
                    break
            except Exception as e:
                logger.debug(f"Sélecteur {selector} non trouvé: {e}")
        
        if not bouton_trouve:
            # Essayer un dernier recours avec JavaScript pour trouver des éléments interactifs
            try:
                logger.info("⚠️ Tentative de recherche avancée des boutons de candidature via JavaScript...")
                js = """
                    // Rechercher tout élément qui ressemble à un bouton de candidature
                    function findCandidatureButton() {
                        // Liste de mots-clés associés aux candidatures
                        const keywords = ['candidature', 'postuler', 'j\'envoie', 'je candidate', 'candidater'];
                        
                        // Rechercher dans tous les boutons et liens
                        const elements = [...document.querySelectorAll('button, a.fr-btn, a.btn, .fr-btn')]
                            .filter(el => {
                                const text = el.textContent.toLowerCase();
                                return keywords.some(keyword => text.includes(keyword.toLowerCase()));
                            });
                        
                        return elements.length > 0 ? elements[0] : null;
                    }
                    return findCandidatureButton();
                """
                js_bouton = driver.execute_script(js)
                if js_bouton:
                    logger.info(f"✅ Bouton trouvé via recherche JavaScript avancée: {js_bouton.text if hasattr(js_bouton, 'text') else 'sans texte'}")
                    driver.execute_script("arguments[0].style.border='3px solid red';", js_bouton)
                    driver.save_screenshot(f"debug_screenshots/bouton_js_trouve_{titre_offre.replace(' ', '_')}.png")
                    js_bouton.click()
                    bouton_trouve = True
                else:
                    logger.warning(f"❌ Impossible de trouver le bouton de candidature pour {titre_offre}")
                    driver.save_screenshot(f"debug_screenshots/bouton_candidature_non_trouve_{titre_offre.replace(' ', '_')}.png")
                    return {"status": "echec", "raison": "bouton_non_trouve"}
            except Exception as e:
                logger.warning(f"❌ Impossible de trouver le bouton de candidature pour {titre_offre}")
                logger.debug(f"Erreur lors de la recherche avancée: {str(e)}")
                driver.save_screenshot(f"debug_screenshots/bouton_candidature_non_trouve_{titre_offre.replace(' ', '_')}.png")
                return {"status": "echec", "raison": "bouton_non_trouve"}
        
        # Attendre l'apparition du formulaire de candidature
        form_selectors = [
            "form",
            ".chakra-modal__body form",
            "//form"
        ]
        
        form_trouve = False
        for selector in form_selectors:
            try:
                if selector.startswith("//"):  # XPath
                    wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                else:  # Sélecteur CSS
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                
                logger.info(f"✅ Formulaire de candidature détecté avec le sélecteur {selector}")
                form_trouve = True
                break
            except Exception as e:
                logger.debug(f"Sélecteur de formulaire {selector} non trouvé: {e}")
        
        if not form_trouve:
            logger.warning(f"❌ Formulaire de candidature non trouvé pour {titre_offre}")
            driver.save_screenshot(f"debug_screenshots/formulaire_non_trouve_{titre_offre.replace(' ', '_')}.png")
            return {"status": "echec", "raison": "formulaire_non_trouve"}
        
        # Formulaire détecté avec succès
        logger.info(f"✅ Candidature initiée pour: {titre_offre}")
        driver.save_screenshot(f"debug_screenshots/formulaire_candidature_{titre_offre.replace(' ', '_')}.png")
        
        # Remplir automatiquement le formulaire si l'option est activée
        result = {"status": "succes"}
        if AUTO_REMPLIR_FORMULAIRE:
            # Récupérer les données utilisateur (par exemple depuis un profil utilisateur)
            user_data = {
                'nom': 'Dupont',
                'prenom': 'Jean',
                'email': 'jean.dupont@example.com',
                'telephone': '0612345678'
            }
            result = remplir_formulaire_candidature(driver, user_data, titre_offre)
        
        # Pause avant soumission si activé
        if PAUSE_AVANT_ENVOI:
            logger.info("Pause avant envoi du formulaire - Attente de 5 secondes pour inspection manuelle...")
            time.sleep(5)  # Attente pour inspection manuelle
        
        # Si l'envoi automatique est activé, soumettre le formulaire
        if AUTO_ENVOYER_CANDIDATURE:
            logger.info("Recherche du bouton d'envoi de candidature...")
            
            # Sélecteurs pour le bouton "J'envoie ma candidature" avec différentes méthodes
            candidature_button = None
            button_found = False
            external_site_redirect = False
            
            # Vérifier d'abord s'il y a un bouton qui redirige vers un site externe
            external_button_selectors = [
                "//button[contains(text(), 'Je postule sur Hellowork')]",
                "//button[contains(., 'Je postule sur Hellowork')]",
                "//button[contains(text(), 'Postuler sur')]",
                "//button[contains(., 'Postuler sur')]",
                "//button[contains(text(), 'Je postule sur')]",
                "//a[contains(text(), 'Je postule sur')]",
                "//a[contains(text(), 'Postuler sur')]"
            ]
            
            # Vérifier si un bouton de redirection externe existe
            for selector in external_button_selectors:
                try:
                    external_button = driver.find_element(By.XPATH, selector)
                    if external_button:
                        button_text = external_button.text.strip()
                        logger.warning(f"⚠️ Détection d'une redirection externe: '{button_text}' - Offre ignorée")
                        driver.save_screenshot(f"debug_screenshots/redirection_externe_{titre_offre.replace(' ', '_')}.png")
                        external_site_redirect = True
                        break
                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.debug(f"Erreur lors de la recherche des boutons externes: {str(e)[:100]}...")
            
            # Si une redirection externe est détectée, on arrête la postulation
            if external_site_redirect:
                return {"status": "ignoré", "raison": "Redirection vers un site externe"}
            
            # Sinon, on recherche le bouton standard de candidature
            button_selectors = [
                # Sélecteurs précis par data-testid
                "button[data-testid='apply-button']",
                "button.fr-btn--secondary[data-testid='apply-button']", 
                
                # Sélecteurs basés sur le texte des boutons (différentes variantes possibles)
                "//button[contains(text(), \"J'envoie ma candidature\")]",
                "//button[contains(text(), \"Je postule\")]",
                "//button[contains(., \"J'envoie ma candidature\")]",
                "//button[contains(., \"Je postule\")]",
                
                # Sélecteurs génériques de boutons avec des classes potentielles
                "button.fr-btn--secondary",
                "button.chakra-button",
                "button.fr-btn",
                
                # Sélecteurs encore plus génériques si tout échoue
                "button[type='button']",
                "//button"
            ]
            
            # Rechercher le bouton "J'envoie ma candidature" avec différentes méthodes
            for selector in button_selectors:
                try:
                    if selector.startswith("//"):  # XPath
                        candidature_button = driver.find_element(By.XPATH, selector)
                    else:  # CSS
                        candidature_button = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if candidature_button:
                        button_text = candidature_button.text.strip()
                        logger.info(f"✅ Bouton 'J'envoie ma candidature' trouvé: '{button_text}'")
                        button_found = True
                        break
                    
                    # Capturer une image du bouton avant clic
                    driver.save_screenshot(f"debug_screenshots/bouton_envoi_trouve_{titre_offre.replace(' ', '_')}.png")
                    
                    # Obtenir le texte du bouton pour le log
                    button_text = submit_button.text.strip()
                    logger.info(f"✅ Bouton d'envoi trouvé: '{button_text}'")
                    
                    # Scroller jusqu'au bouton pour s'assurer qu'il est visible
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", submit_button)
                    time.sleep(1)  # Attendre que le scroll soit terminé
                    
                    # Cliquer sur le bouton d'envoi
                    logger.info("Clic sur le bouton d'envoi de candidature...")
                    
                    # Tentative de clic de différentes manières pour maximiser les chances de succès
                    try:
                        # Méthode 1: clic standard
                        submit_button.click()
                    except Exception as click_error:
                        logger.debug(f"Clic standard a échoué: {str(click_error)[:100]}...")
                        try:
                            # Méthode 2: clic via JavaScript
                            driver.execute_script("arguments[0].click();", submit_button)
                        except Exception as js_error:
                            logger.debug(f"Clic JavaScript a échoué: {str(js_error)[:100]}...")
                            try:
                                # Méthode 3: clic via Actions
                                ActionChains(driver).move_to_element(submit_button).click().perform()
                            except Exception as action_error:
                                logger.error(f"Toutes les tentatives de clic ont échoué: {str(action_error)[:100]}...")
                                driver.save_screenshot(f"debug_screenshots/erreur_clic_bouton_envoi_{titre_offre.replace(' ', '_')}.png")
                    
                    # Attendre un moment pour que la soumission soit traitée
                    time.sleep(3)
                    
                    # Tenter de détecter une confirmation de succès
                    try:
                        success_indicators = [
                            ".fr-alert--success",  # Alerte de succès
                            "//div[contains(text(), 'Candidature envoyée')]",  # Message de confirmation
                            "//p[contains(text(), 'succès')]",  # Texte contenant "succès"
                            "//div[contains(@class, 'success')]",  # Classe contenant "success"
                            "//div[@role='alert' and contains(@class, 'success')]",  # Alerte avec classe de succès
                        ]
                        
                        success_found = False
                        for indicator in success_indicators:
                            try:
                                if indicator.startswith("//"):  # XPath
                                    confirmation = driver.find_element(By.XPATH, indicator)
                                else:  # CSS
                                    confirmation = driver.find_element(By.CSS_SELECTOR, indicator)
                                
                                # Mettre en évidence l'élément de confirmation
                                driver.execute_script("arguments[0].style.border='3px solid green';", confirmation)
                                success_found = True
                                logger.info(f"✅ Confirmation de candidature détectée: '{confirmation.text}'")
                                break
                            except:
                                continue
                        
                        if success_found:
                            logger.info("✅ CANDIDATURE ENVOYÉE AVEC SUCCÈS!")
                            driver.save_screenshot(f"debug_screenshots/candidature_success_{titre_offre.replace(' ', '_')}.png")
                        else:
                            logger.info("ℹ️ Candidature probablement envoyée, mais pas de message de confirmation explicite détecté")
                    except Exception as e:
                        logger.debug(f"Erreur lors de la vérification de confirmation: {str(e)[:100]}...")
                    
                    submit_button_found = True
                    break
                except Exception as e:
                    logger.debug(f"Sélecteur {selector} pour bouton d'envoi non trouvé: {str(e)[:100]}...")
            
            if not submit_button_found:
                logger.warning("❌ Aucun bouton d'envoi de candidature trouvé - vérifier la structure DOM")
                driver.save_screenshot(f"debug_screenshots/bouton_envoi_non_trouve_{titre_offre.replace(' ', '_')}.png")
        else:
            logger.info("ℹ️ Mode automatique désactivé - candidature prête mais non envoyée")
            driver.save_screenshot(f"debug_screenshots/candidature_prete_non_envoyee_{titre_offre.replace(' ', '_')}.png")
        
        # Prendre une capture d'écran finale
        try:
            driver.save_screenshot(f"debug_screenshots/fin_processus_{titre_offre.replace(' ', '_')}.png")
            logger.info("✅ Capture d'écran finale effectuée")
        except Exception as e:
            logger.debug(f"Impossible de prendre la capture d'écran finale: {str(e)[:100]}...")
            
        return {"status": "success", "formulaire_rempli": True, "formulaire_soumis": AUTO_ENVOYER_CANDIDATURE}
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la tentative de postulation pour {titre_offre}: {str(e)}")
        logger.error("Trace complète:", exc_info=True)
        driver.save_screenshot(f"debug_screenshots/erreur_postulation_{titre_offre.replace(' ', '_')}.png")
        return {"status": "erreur", "raison": str(e)}
    finally:
        # Revenir à l'onglet principal
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

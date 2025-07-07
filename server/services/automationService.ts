import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { storage } from '../storage';
import { AutomationSession, AutomationSettings, UserConfig } from '@shared/schema';

class AutomationService {
  private currentProcess: ChildProcess | null = null;
  private currentSession: AutomationSession | null = null;
  private broadcast: ((data: any) => void) | null = null;

  setBroadcast(broadcastFn: (data: any) => void) {
    this.broadcast = broadcastFn;
  }

  private emitUpdate(type: string, data: any) {
    if (this.broadcast) {
      this.broadcast({ type, data });
    }
  }

  async startAutomation(): Promise<AutomationSession> {
    // Check if already running
    const existingSession = await storage.getCurrentSession();
    if (existingSession) {
      throw new Error('Une session d\'automatisation est déjà en cours');
    }

    // Get user config and settings
    const userConfig = await storage.getUserConfig();
    if (!userConfig) {
      throw new Error('Configuration utilisateur manquante. Veuillez remplir vos informations personnelles.');
    }

    if (!userConfig.cvPath || !userConfig.coverLetterPath) {
      throw new Error('Documents manquants. Veuillez uploader votre CV et lettre de motivation.');
    }

    let settings = await storage.getAutomationSettings();
    if (!settings) {
      // Create default settings if none exist
      settings = await storage.createAutomationSettings({
        delayBetweenApplications: 30,
        maxApplicationsPerSession: 50,
        autoFillForm: true,
        autoSendApplication: true,
        pauseBeforeSend: false,
        captureScreenshots: true,
      });
    }

    // Create new session
    const session = await storage.createAutomationSession({
      status: 'running',
      userConfigId: userConfig.id,
      settings: settings,
    });

    this.currentSession = session;

    try {
      // Start demo automation process directly without Python
      this.emitUpdate('session_started', session);
      
      // Start the demo automation in the background
      setTimeout(async () => {
        await this.startRealAutomation(userConfig, settings, session);
      }, 1000);
      
      return session;
    } catch (error) {
      // If automation fails, update session status
      await storage.updateAutomationSession(session.id, {
        status: 'stopped',
        endedAt: new Date(),
      });
      this.currentSession = null;
      throw error;
    }
  }

  async pauseAutomation(): Promise<AutomationSession> {
    const session = await storage.getCurrentSession();
    if (!session) {
      throw new Error('No active automation session');
    }

    if (this.currentProcess) {
      // Send pause signal to Python process
      this.currentProcess.kill('SIGTERM');
      this.currentProcess = null;
    }

    const updatedSession = await storage.updateAutomationSession(session.id, {
      status: 'paused',
    });

    this.currentSession = updatedSession;
    this.emitUpdate('session_paused', updatedSession);
    return updatedSession;
  }

  async stopAutomation(): Promise<AutomationSession> {
    const session = await storage.getCurrentSession();
    if (!session) {
      throw new Error('No active automation session');
    }

    if (this.currentProcess) {
      this.currentProcess.kill('SIGKILL');
      this.currentProcess = null;
    }

    const updatedSession = await storage.updateAutomationSession(session.id, {
      status: 'stopped',
      endedAt: new Date(),
    });

    this.currentSession = null;
    this.emitUpdate('session_stopped', updatedSession);
    return updatedSession;
  }

  async getStatus(): Promise<{
    isRunning: boolean;
    currentSession: AutomationSession | null;
    statistics: {
      totalApplications: number;
      successfulApplications: number;
      failedApplications: number;
      elapsedTime: number;
    };
  }> {
    const session = await storage.getCurrentSession();
    const isRunning = session?.status === 'running';

    let statistics = {
      totalApplications: 0,
      successfulApplications: 0,
      failedApplications: 0,
      elapsedTime: 0,
    };

    if (session) {
      statistics = {
        totalApplications: session.totalApplications || 0,
        successfulApplications: session.successfulApplications || 0,
        failedApplications: session.failedApplications || 0,
        elapsedTime: session.startedAt ? Date.now() - new Date(session.startedAt).getTime() : 0,
      };
    }

    return {
      isRunning,
      currentSession: session || null,
      statistics,
    };
  }

  // Remove Python process dependency

  private async handlePythonOutput(output: string) {
    try {
      const lines = output.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        if (line.startsWith('JSON:')) {
          const jsonData = JSON.parse(line.substring(5));
          await this.processPythonMessage(jsonData);
        } else {
          // Regular log output
          await this.createLog('info', line);
        }
      }
    } catch (error) {
      await this.createLog('error', `Failed to process Python output: ${error}`);
    }
  }

  private async handlePythonError(error: string) {
    await this.createLog('error', error);
    this.emitUpdate('automation_error', { error });
  }

  private async handlePythonClose(code: number | null) {
    if (this.currentSession) {
      const status = code === 0 ? 'completed' : 'stopped';
      const updatedSession = await storage.updateAutomationSession(this.currentSession.id, {
        status,
        endedAt: new Date(),
      });
      this.emitUpdate('session_ended', updatedSession);
    }
    this.currentProcess = null;
    this.currentSession = null;
  }

  private async processPythonMessage(message: any) {
    switch (message.type) {
      case 'application_started':
        await this.createApplication(message.data);
        break;
      case 'application_completed':
        await this.updateApplication(message.data);
        break;
      case 'screenshot_captured':
        await this.createScreenshot(message.data);
        break;
      case 'session_stats':
        await this.updateSessionStats(message.data);
        break;
      case 'log':
        await this.createLog(message.data.level, message.data.message, message.data.metadata);
        break;
      default:
        await this.createLog('debug', `Unknown message type: ${message.type}`);
    }
  }

  private async createApplication(data: any) {
    if (!this.currentSession) return;

    const application = await storage.createApplication({
      sessionId: this.currentSession.id,
      jobTitle: data.jobTitle,
      company: data.company,
      location: data.location,
      status: 'pending',
    });

    this.emitUpdate('application_started', application);
  }

  private async updateApplication(data: any) {
    const applications = await storage.getApplications();
    const application = applications.find(app => 
      app.jobTitle === data.jobTitle && app.company === data.company
    );

    if (application) {
      const updated = await storage.updateApplication(application.id, {
        status: data.status,
        errorMessage: data.errorMessage,
        screenshotPath: data.screenshotPath,
      });

      this.emitUpdate('application_updated', updated);
    }
  }

  private async createScreenshot(data: any) {
    if (!this.currentSession) return;

    const screenshot = await storage.createScreenshot({
      sessionId: this.currentSession.id,
      applicationId: data.applicationId,
      filePath: data.filePath,
      description: data.description,
    });

    this.emitUpdate('screenshot_captured', screenshot);
  }

  private async updateSessionStats(data: any) {
    if (!this.currentSession) return;

    const updated = await storage.updateAutomationSession(this.currentSession.id, {
      totalApplications: data.totalApplications,
      successfulApplications: data.successfulApplications,
      failedApplications: data.failedApplications,
    });

    this.currentSession = updated;
    this.emitUpdate('session_stats_updated', updated);
  }

  private async createLog(level: string, message: string, metadata?: any) {
    if (!this.currentSession) return;

    const log = await storage.createAutomationLog({
      sessionId: this.currentSession.id,
      level,
      message,
      metadata,
    });

    this.emitUpdate('log_created', log);
  }

  private async startRealAutomation(userConfig: UserConfig, settings: AutomationSettings, session: AutomationSession) {
    // Start real Python automation using actual scripts
    await this.createLog('info', 'Démarrage de l\'automatisation réelle...');
    
    try {
      // Create user data object for Python script
      const userData = {
        firstName: userConfig.firstName,
        lastName: userConfig.lastName,
        email: userConfig.email,
        phone: userConfig.phone,
        message: userConfig.message,
        cvPath: userConfig.cvPath,
        coverLetterPath: userConfig.coverLetterPath,
        searchKeywords: userConfig.searchKeywords,
        searchLocation: userConfig.searchLocation,
        contractTypes: userConfig.contractTypes,
        educationLevel: userConfig.educationLevel,
        searchRadius: userConfig.searchRadius,
        settings: {
          delayBetweenApplications: settings.delayBetweenApplications || 30,
          maxApplicationsPerSession: settings.maxApplicationsPerSession || 10,
          autoFillForm: settings.autoFillForm ?? true,
          autoSendApplication: settings.autoSendApplication ?? true,
          pauseBeforeSend: settings.pauseBeforeSend ?? false,
          captureScreenshots: settings.captureScreenshots ?? true
        }
      };
      
      // Path to the Python automation runner script
      const pythonScript = path.join(process.cwd(), 'python_scripts', 'automation_runner.py');
      
      await this.createLog('info', 'Lancement du script Python d\'automatisation...');
      
      // Start Python process
      this.currentProcess = spawn('python3', [pythonScript], {
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe'],
        env: {
          ...process.env,
          AUTOMATION_SESSION_ID: session.id.toString(),
          USER_CONFIG: JSON.stringify(userData)
        }
      });
      
      // Send user data to Python script
      if (this.currentProcess.stdin) {
        this.currentProcess.stdin.write(JSON.stringify(userData) + '\n');
        this.currentProcess.stdin.end();
      }
      
      // Handle Python script output
      if (this.currentProcess.stdout) {
        this.currentProcess.stdout.on('data', (data) => {
          const output = data.toString();
          this.handlePythonOutput(output);
        });
      }
      
      if (this.currentProcess.stderr) {
        this.currentProcess.stderr.on('data', (data) => {
          const error = data.toString();
          this.handlePythonError(error);
        });
      }
      
      this.currentProcess.on('close', (code) => {
        this.handlePythonClose(code);
      });
      
      await this.createLog('info', 'Script Python démarré, connexion à alternance.gouv.fr...');
      
    } catch (error) {
      await this.createLog('error', `Erreur lors du démarrage de l'automatisation: ${error}`);
      
      // Mark session as failed
      await storage.updateAutomationSession(session.id, {
        status: 'failed',
        endedAt: new Date()
      });
      
      this.currentSession = null;
      throw error;
    }
  }

  // Fallback method for demonstration when Python is not available
  private async startDemoAutomation(userConfig: UserConfig, settings: AutomationSettings, session: AutomationSession) {
    await this.createLog('warning', 'Mode démonstration - Python non disponible, utilisation de données simulées');
    
    // Generate job offers based on user preferences
    const mockOffers = this.generateJobOffers(userConfig);
    
    if (mockOffers.length === 0) {
      await this.createLog('warning', 'Aucune offre trouvée correspondant à vos critères. Utilisation des critères par défaut.');
      // Use default offers if no preferences are set
      mockOffers.push(
        {
          title: 'Développeur Full Stack - Alternance',
          company: 'TechCorp SAS',
          location: 'Paris, France',
          url: 'https://alternance.gouv.fr/offre/123'
        },
        {
          title: 'Développeur React - Stage',
          company: 'InnovateLab',
          location: 'Lyon, France',
          url: 'https://alternance.gouv.fr/offre/124'
        }
      );
    }

    await this.createLog('success', `${mockOffers.length} offres d'alternance trouvées`);

    // Process each offer with delays
    for (let i = 0; i < mockOffers.length; i++) {
      if (!this.currentSession || this.currentSession.status !== 'running') {
        break;
      }

      const offer = mockOffers[i];
      await this.createLog('info', `Traitement de l'offre ${i + 1}/${mockOffers.length}: ${offer.title}`);

      // Create application record
      const application = await storage.createApplication({
        sessionId: session.id,
        jobTitle: offer.title,
        company: offer.company,
        location: offer.location,
        status: 'pending',
      });

      this.emitUpdate('application_started', application);

      // Simulate application process with realistic timing
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 seconds for processing
      
      // Simulate different failure scenarios with realistic reasons
      const scenarioRand = Math.random();
      let isSuccess = true;
      let errorMessage = '';
      
      if (scenarioRand < 0.05) {
        // 5% - Redirection vers un site externe
        isSuccess = false;
        errorMessage = 'Offre redirige vers un site externe (non alternance.gouv.fr)';
      } else if (scenarioRand < 0.08) {
        // 3% - Formation au lieu d'alternance
        isSuccess = false;
        errorMessage = 'Il s\'agit d\'une formation, pas d\'une offre d\'alternance';
      } else if (scenarioRand < 0.12) {
        // 4% - Formulaire non accessible
        isSuccess = false;
        errorMessage = 'Formulaire de candidature temporairement indisponible';
      } else if (scenarioRand < 0.15) {
        // 3% - Offre expirée
        isSuccess = false;
        errorMessage = 'Offre expirée ou pourvue';
      } else if (scenarioRand < 0.18) {
        // 3% - Problème technique
        isSuccess = false;
        errorMessage = 'Erreur technique lors du remplissage du formulaire';
      }
      // 82% de succès
      
      if (isSuccess) {
        await storage.updateApplication(application.id, {
          status: 'sent',
        });
        this.emitUpdate('application_updated', { ...application, status: 'sent' });
        await this.createLog('success', `Candidature envoyée avec succès pour: ${offer.title} chez ${offer.company}`);
      } else {
        await storage.updateApplication(application.id, {
          status: 'failed',
          errorMessage: errorMessage,
        });
        this.emitUpdate('application_updated', { ...application, status: 'failed', errorMessage: errorMessage });
        await this.createLog('error', `Échec de candidature pour: ${offer.title} - ${errorMessage}`);
      }

      // Update session statistics
      const updatedSession = await storage.updateAutomationSession(session.id, {
        totalApplications: i + 1,
        successfulApplications: isSuccess ? (session.successfulApplications || 0) + 1 : session.successfulApplications,
        failedApplications: !isSuccess ? (session.failedApplications || 0) + 1 : session.failedApplications,
      });

      this.currentSession = updatedSession;
      this.emitUpdate('session_stats_updated', updatedSession);

      // Create mock screenshot
      await storage.createScreenshot({
        sessionId: session.id,
        applicationId: application.id,
        filePath: `debug_screenshots/demo_application_${application.id}.png`,
        description: `Candidature ${offer.title} - ${offer.company}`,
      });

      this.emitUpdate('screenshot_captured', {
        filePath: `debug_screenshots/demo_application_${application.id}.png`,
        description: `Candidature ${offer.title} - ${offer.company}`,
        applicationId: application.id,
      });

      // Wait between applications (configurable delay)
      if (i < mockOffers.length - 1) {
        const delay = settings.delayBetweenApplications || 30;
        await this.createLog('info', `Attente de ${delay} secondes avant la prochaine candidature...`);
        await new Promise(resolve => setTimeout(resolve, delay * 1000));
      }
    }

    // Complete the session
    await storage.updateAutomationSession(session.id, {
      status: 'completed',
      endedAt: new Date(),
    });

    this.currentSession = null;
    this.emitUpdate('session_ended', { status: 'completed' });
    await this.createLog('success', 'Session d\'automatisation terminée avec succès');
  }

  private generateJobOffers(userConfig: UserConfig) {
    const offers = [];
    
    const keywords = userConfig.searchKeywords?.toLowerCase() || '';
    const locations = userConfig.searchLocation?.toLowerCase() || '';
    const jobTypes = userConfig.jobTypes?.toLowerCase() || '';
    const educationLevel = userConfig.educationLevel?.toLowerCase() || '';
    const searchRadius = userConfig.searchRadius || '30';

    // Log the search criteria
    if (keywords) {
      this.createLog('info', `Recherche avec mots-clés: ${keywords}`);
    }
    if (locations) {
      this.createLog('info', `Recherche dans les villes: ${locations}`);
    }

    // Generate offers based on keywords
    if (keywords.includes('développeur') || keywords.includes('dev') || keywords.includes('programmeur')) {
      if (keywords.includes('web') || keywords.includes('frontend') || keywords.includes('react') || keywords.includes('javascript')) {
        offers.push({
          title: 'Développeur Frontend React - Alternance',
          company: 'WebTech Solutions',
          location: this.getLocationFromPreferences(locations) || 'Paris, France',
          url: 'https://alternance.gouv.fr/offre/dev-frontend-001'
        });
      }
      
      if (keywords.includes('full stack') || keywords.includes('fullstack')) {
        offers.push({
          title: 'Développeur Full Stack - Alternance',
          company: 'TechCorp SAS',
          location: this.getLocationFromPreferences(locations) || 'Lyon, France',
          url: 'https://alternance.gouv.fr/offre/dev-fullstack-001'
        });
      }
      
      if (keywords.includes('backend') || keywords.includes('python') || keywords.includes('node')) {
        offers.push({
          title: 'Développeur Backend Python - Alternance',
          company: 'DataFlow Systems',
          location: this.getLocationFromPreferences(locations) || 'Marseille, France',
          url: 'https://alternance.gouv.fr/offre/dev-backend-001'
        });
      }
      
      if (keywords.includes('mobile') || keywords.includes('android') || keywords.includes('ios')) {
        offers.push({
          title: 'Développeur Mobile React Native - Alternance',
          company: 'MobileFirst Studio',
          location: this.getLocationFromPreferences(locations) || 'Toulouse, France',
          url: 'https://alternance.gouv.fr/offre/dev-mobile-001'
        });
      }
    }

    if (keywords.includes('devops') || keywords.includes('infrastructure') || keywords.includes('cloud')) {
      offers.push({
        title: 'Ingénieur DevOps Junior - Alternance',
        company: 'CloudTech',
        location: this.getLocationFromPreferences(locations) || 'Nantes, France',
        url: 'https://alternance.gouv.fr/offre/devops-001'
      });
    }

    if (keywords.includes('data') || keywords.includes('analyse') || keywords.includes('machine learning')) {
      offers.push({
        title: 'Data Analyst - Alternance',
        company: 'DataInsights Corp',
        location: this.getLocationFromPreferences(locations) || 'Bordeaux, France',
        url: 'https://alternance.gouv.fr/offre/data-001'
      });
    }

    if (keywords.includes('design') || keywords.includes('ui') || keywords.includes('ux')) {
      offers.push({
        title: 'Designer UX/UI - Alternance',
        company: 'Design Studio Pro',
        location: this.getLocationFromPreferences(locations) || 'Nice, France',
        url: 'https://alternance.gouv.fr/offre/design-001'
      });
    }

    return offers;
  }

  private getLocationFromPreferences(locationPrefs: string): string | null {
    if (!locationPrefs) return null;
    
    const cities = ['paris', 'lyon', 'marseille', 'toulouse', 'nantes', 'strasbourg', 'montpellier', 'bordeaux', 'lille', 'rennes'];
    
    for (const city of cities) {
      if (locationPrefs.includes(city)) {
        return city.charAt(0).toUpperCase() + city.slice(1) + ', France';
      }
    }
    
    return null;
  }
}

export const automationService = new AutomationService();

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
      throw new Error('Automation is already running');
    }

    // Get user config and settings
    const userConfig = await storage.getUserConfig();
    if (!userConfig) {
      throw new Error('User configuration not found');
    }

    const settings = await storage.getAutomationSettings();
    if (!settings) {
      throw new Error('Automation settings not found');
    }

    // Create new session
    const session = await storage.createAutomationSession({
      status: 'running',
      userConfigId: userConfig.id,
      settings: settings,
    });

    this.currentSession = session;

    // Start Python automation process
    await this.startPythonProcess(userConfig, settings, session);

    this.emitUpdate('session_started', session);
    return session;
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
      currentSession: session,
      statistics,
    };
  }

  private async startPythonProcess(userConfig: UserConfig, settings: AutomationSettings, session: AutomationSession) {
    const pythonScriptPath = path.join(process.cwd(), 'python_scripts', 'automation_runner.py');

    const args = [
      pythonScriptPath,
      '--session-id', session.id.toString(),
      '--user-config', JSON.stringify(userConfig),
      '--settings', JSON.stringify(settings),
    ];

    this.currentProcess = spawn('python3', args, {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env,
    });

    this.currentProcess.stdout?.on('data', (data) => {
      this.handlePythonOutput(data.toString());
    });

    this.currentProcess.stderr?.on('data', (data) => {
      this.handlePythonError(data.toString());
    });

    this.currentProcess.on('close', (code) => {
      this.handlePythonClose(code);
    });

    this.currentProcess.on('error', (error) => {
      this.handlePythonError(error.message);
    });
  }

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
}

export const automationService = new AutomationService();

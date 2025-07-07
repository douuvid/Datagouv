import { 
  userConfigs, 
  automationSessions, 
  applications, 
  automationLogs, 
  screenshots, 
  automationSettings,
  type UserConfig,
  type InsertUserConfig,
  type AutomationSession,
  type InsertAutomationSession,
  type Application,
  type InsertApplication,
  type AutomationLog,
  type InsertAutomationLog,
  type Screenshot,
  type InsertScreenshot,
  type AutomationSettings,
  type InsertAutomationSettings
} from "@shared/schema";

export interface IStorage {
  // User Config
  getUserConfig(): Promise<UserConfig | undefined>;
  createUserConfig(config: InsertUserConfig): Promise<UserConfig>;
  updateUserConfig(config: Partial<UserConfig>): Promise<UserConfig>;

  // Automation Sessions
  getAutomationSessions(): Promise<AutomationSession[]>;
  getCurrentSession(): Promise<AutomationSession | undefined>;
  createAutomationSession(session: InsertAutomationSession): Promise<AutomationSession>;
  updateAutomationSession(id: number, session: Partial<AutomationSession>): Promise<AutomationSession>;

  // Applications
  getApplications(sessionId?: number): Promise<Application[]>;
  createApplication(application: InsertApplication): Promise<Application>;
  updateApplication(id: number, application: Partial<Application>): Promise<Application>;

  // Automation Logs
  getAutomationLogs(sessionId?: number): Promise<AutomationLog[]>;
  createAutomationLog(log: InsertAutomationLog): Promise<AutomationLog>;
  clearAutomationLogs(sessionId?: number): Promise<void>;

  // Screenshots
  getScreenshots(sessionId?: number): Promise<Screenshot[]>;
  createScreenshot(screenshot: InsertScreenshot): Promise<Screenshot>;

  // Automation Settings
  getAutomationSettings(): Promise<AutomationSettings | undefined>;
  createAutomationSettings(settings: InsertAutomationSettings): Promise<AutomationSettings>;
  updateAutomationSettings(settings: Partial<AutomationSettings>): Promise<AutomationSettings>;
}

export class MemStorage implements IStorage {
  private userConfigs: Map<number, UserConfig> = new Map();
  private automationSessions: Map<number, AutomationSession> = new Map();
  private applications: Map<number, Application> = new Map();
  private automationLogs: Map<number, AutomationLog> = new Map();
  private screenshots: Map<number, Screenshot> = new Map();
  private automationSettings: Map<number, AutomationSettings> = new Map();
  private currentId: number = 1;

  private getNextId(): number {
    return this.currentId++;
  }

  // User Config
  async getUserConfig(): Promise<UserConfig | undefined> {
    return Array.from(this.userConfigs.values())[0];
  }

  async createUserConfig(config: InsertUserConfig): Promise<UserConfig> {
    const id = this.getNextId();
    const userConfig = {
      ...config,
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
    } as UserConfig;
    this.userConfigs.set(id, userConfig);
    return userConfig;
  }

  async updateUserConfig(config: Partial<UserConfig>): Promise<UserConfig> {
    const existing = await this.getUserConfig();
    if (!existing) {
      throw new Error("User config not found");
    }
    const updated: UserConfig = {
      ...existing,
      ...config,
      updatedAt: new Date(),
    };
    this.userConfigs.set(existing.id, updated);
    return updated;
  }

  // Automation Sessions
  async getAutomationSessions(): Promise<AutomationSession[]> {
    return Array.from(this.automationSessions.values()).sort((a, b) => 
      new Date(b.startedAt!).getTime() - new Date(a.startedAt!).getTime()
    );
  }

  async getCurrentSession(): Promise<AutomationSession | undefined> {
    return Array.from(this.automationSessions.values()).find(
      session => session.status === 'running' || session.status === 'paused'
    );
  }

  async createAutomationSession(session: InsertAutomationSession): Promise<AutomationSession> {
    const id = this.getNextId();
    const automationSession = {
      ...session,
      id,
      startedAt: new Date(),
      endedAt: null,
      totalApplications: 0,
      successfulApplications: 0,
      failedApplications: 0,
    } as AutomationSession;
    this.automationSessions.set(id, automationSession);
    return automationSession;
  }

  async updateAutomationSession(id: number, session: Partial<AutomationSession>): Promise<AutomationSession> {
    const existing = this.automationSessions.get(id);
    if (!existing) {
      throw new Error("Automation session not found");
    }
    const updated: AutomationSession = {
      ...existing,
      ...session,
    };
    this.automationSessions.set(id, updated);
    return updated;
  }

  // Applications
  async getApplications(sessionId?: number): Promise<Application[]> {
    const apps = Array.from(this.applications.values());
    if (sessionId) {
      return apps.filter(app => app.sessionId === sessionId);
    }
    return apps.sort((a, b) => new Date(b.appliedAt!).getTime() - new Date(a.appliedAt!).getTime());
  }

  async createApplication(application: InsertApplication): Promise<Application> {
    const id = this.getNextId();
    const app = {
      ...application,
      id,
      appliedAt: new Date(),
    } as Application;
    this.applications.set(id, app);
    return app;
  }

  async updateApplication(id: number, application: Partial<Application>): Promise<Application> {
    const existing = this.applications.get(id);
    if (!existing) {
      throw new Error("Application not found");
    }
    const updated: Application = {
      ...existing,
      ...application,
    };
    this.applications.set(id, updated);
    return updated;
  }

  // Automation Logs
  async getAutomationLogs(sessionId?: number): Promise<AutomationLog[]> {
    const logs = Array.from(this.automationLogs.values());
    if (sessionId) {
      return logs.filter(log => log.sessionId === sessionId);
    }
    return logs.sort((a, b) => new Date(b.timestamp!).getTime() - new Date(a.timestamp!).getTime());
  }

  async createAutomationLog(log: InsertAutomationLog): Promise<AutomationLog> {
    const id = this.getNextId();
    const automationLog = {
      ...log,
      id,
      timestamp: new Date(),
    } as AutomationLog;
    this.automationLogs.set(id, automationLog);
    return automationLog;
  }

  async clearAutomationLogs(sessionId?: number): Promise<void> {
    if (sessionId) {
      Array.from(this.automationLogs.entries()).forEach(([id, log]) => {
        if (log.sessionId === sessionId) {
          this.automationLogs.delete(id);
        }
      });
    } else {
      this.automationLogs.clear();
    }
  }

  // Screenshots
  async getScreenshots(sessionId?: number): Promise<Screenshot[]> {
    const screenshots = Array.from(this.screenshots.values());
    if (sessionId) {
      return screenshots.filter(screenshot => screenshot.sessionId === sessionId);
    }
    return screenshots.sort((a, b) => new Date(b.capturedAt!).getTime() - new Date(a.capturedAt!).getTime());
  }

  async createScreenshot(screenshot: InsertScreenshot): Promise<Screenshot> {
    const id = this.getNextId();
    const screenshotRecord = {
      ...screenshot,
      id,
      capturedAt: new Date(),
    } as Screenshot;
    this.screenshots.set(id, screenshotRecord);
    return screenshotRecord;
  }

  // Automation Settings
  async getAutomationSettings(): Promise<AutomationSettings | undefined> {
    return Array.from(this.automationSettings.values())[0];
  }

  async createAutomationSettings(settings: InsertAutomationSettings): Promise<AutomationSettings> {
    const id = this.getNextId();
    const automationSettings = {
      ...settings,
      id,
      createdAt: new Date(),
      updatedAt: new Date(),
    } as AutomationSettings;
    this.automationSettings.set(id, automationSettings);
    return automationSettings;
  }

  async updateAutomationSettings(settings: Partial<AutomationSettings>): Promise<AutomationSettings> {
    const existing = await this.getAutomationSettings();
    if (!existing) {
      throw new Error("Automation settings not found");
    }
    const updated: AutomationSettings = {
      ...existing,
      ...settings,
      updatedAt: new Date(),
    };
    this.automationSettings.set(existing.id, updated);
    return updated;
  }
}

export const storage = new MemStorage();

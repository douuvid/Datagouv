import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import multer from "multer";
import path from "path";
import { storage } from "./storage";
import { automationService } from "./services/automationService";
import { fileService } from "./services/fileService";
import { insertUserConfigSchema, insertAutomationSettingsSchema } from "@shared/schema";

const upload = multer({ dest: 'uploads/' });

export async function registerRoutes(app: Express): Promise<Server> {
  const httpServer = createServer(app);

  // WebSocket server for real-time updates
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  const clients = new Set<WebSocket>();

  wss.on('connection', (ws) => {
    clients.add(ws);
    console.log('Client connected to WebSocket');

    ws.on('close', () => {
      clients.delete(ws);
      console.log('Client disconnected from WebSocket');
    });
  });

  // Broadcast function for real-time updates
  const broadcast = (data: any) => {
    clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(data));
      }
    });
  };

  // Set up automation service with broadcast callback
  automationService.setBroadcast(broadcast);

  // User Configuration Routes
  app.get('/api/user-config', async (req, res) => {
    try {
      const config = await storage.getUserConfig();
      res.json(config);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get user config' });
    }
  });

  app.post('/api/user-config', async (req, res) => {
    try {
      const config = insertUserConfigSchema.parse(req.body);
      const existing = await storage.getUserConfig();
      
      let result;
      if (existing) {
        result = await storage.updateUserConfig(config);
      } else {
        result = await storage.createUserConfig(config);
      }
      
      res.json(result);
    } catch (error) {
      res.status(400).json({ error: 'Invalid user config data' });
    }
  });

  // Document Upload Routes
  app.post('/api/upload/cv', upload.single('cv'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
      }
      
      const filePath = await fileService.saveDocument(req.file, 'cv');
      const userConfig = await storage.getUserConfig();
      
      if (userConfig) {
        await storage.updateUserConfig({ cvPath: filePath });
      }
      
      res.json({ filePath });
    } catch (error) {
      res.status(500).json({ error: 'Failed to upload CV' });
    }
  });

  app.post('/api/upload/cover-letter', upload.single('coverLetter'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
      }
      
      const filePath = await fileService.saveDocument(req.file, 'cover-letter');
      const userConfig = await storage.getUserConfig();
      
      if (userConfig) {
        await storage.updateUserConfig({ coverLetterPath: filePath });
      }
      
      res.json({ filePath });
    } catch (error) {
      res.status(500).json({ error: 'Failed to upload cover letter' });
    }
  });

  // Automation Control Routes
  app.post('/api/automation/start', async (req, res) => {
    try {
      const session = await automationService.startAutomation();
      res.json(session);
    } catch (error) {
      res.status(500).json({ error: 'Failed to start automation' });
    }
  });

  app.post('/api/automation/pause', async (req, res) => {
    try {
      const session = await automationService.pauseAutomation();
      res.json(session);
    } catch (error) {
      res.status(500).json({ error: 'Failed to pause automation' });
    }
  });

  app.post('/api/automation/stop', async (req, res) => {
    try {
      const session = await automationService.stopAutomation();
      res.json(session);
    } catch (error) {
      res.status(500).json({ error: 'Failed to stop automation' });
    }
  });

  app.get('/api/automation/status', async (req, res) => {
    try {
      const status = await automationService.getStatus();
      res.json(status);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get automation status' });
    }
  });

  // Applications Routes
  app.get('/api/applications', async (req, res) => {
    try {
      const sessionId = req.query.sessionId ? parseInt(req.query.sessionId as string) : undefined;
      const applications = await storage.getApplications(sessionId);
      res.json(applications);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get applications' });
    }
  });

  // Logs Routes
  app.get('/api/logs', async (req, res) => {
    try {
      const sessionId = req.query.sessionId ? parseInt(req.query.sessionId as string) : undefined;
      const logs = await storage.getAutomationLogs(sessionId);
      res.json(logs);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get logs' });
    }
  });

  app.delete('/api/logs', async (req, res) => {
    try {
      const sessionId = req.query.sessionId ? parseInt(req.query.sessionId as string) : undefined;
      await storage.clearAutomationLogs(sessionId);
      res.json({ success: true });
    } catch (error) {
      res.status(500).json({ error: 'Failed to clear logs' });
    }
  });

  app.get('/api/logs/export', async (req, res) => {
    try {
      const sessionId = req.query.sessionId ? parseInt(req.query.sessionId as string) : undefined;
      const logs = await storage.getAutomationLogs(sessionId);
      const exportData = await fileService.exportLogs(logs);
      
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename="automation_logs.json"');
      res.send(exportData);
    } catch (error) {
      res.status(500).json({ error: 'Failed to export logs' });
    }
  });

  // Screenshots Routes
  app.get('/api/screenshots', async (req, res) => {
    try {
      const sessionId = req.query.sessionId ? parseInt(req.query.sessionId as string) : undefined;
      const screenshots = await storage.getScreenshots(sessionId);
      res.json(screenshots);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get screenshots' });
    }
  });

  app.get('/api/screenshots/:id', async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      const screenshots = await storage.getScreenshots();
      const screenshot = screenshots.find(s => s.id === id);
      
      if (!screenshot) {
        return res.status(404).json({ error: 'Screenshot not found' });
      }
      
      res.sendFile(path.resolve(screenshot.filePath));
    } catch (error) {
      res.status(500).json({ error: 'Failed to get screenshot' });
    }
  });

  // Automation Settings Routes
  app.get('/api/settings', async (req, res) => {
    try {
      const settings = await storage.getAutomationSettings();
      res.json(settings);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get settings' });
    }
  });

  app.post('/api/settings', async (req, res) => {
    try {
      const settings = insertAutomationSettingsSchema.parse(req.body);
      const existing = await storage.getAutomationSettings();
      
      let result;
      if (existing) {
        result = await storage.updateAutomationSettings(settings);
      } else {
        result = await storage.createAutomationSettings(settings);
      }
      
      res.json(result);
    } catch (error) {
      res.status(400).json({ error: 'Invalid settings data' });
    }
  });

  // Sessions Routes
  app.get('/api/sessions', async (req, res) => {
    try {
      const sessions = await storage.getAutomationSessions();
      res.json(sessions);
    } catch (error) {
      res.status(500).json({ error: 'Failed to get sessions' });
    }
  });

  return httpServer;
}

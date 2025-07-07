import fs from 'fs';
import path from 'path';
import { AutomationLog } from '@shared/schema';

class FileService {
  private uploadsDir = path.join(process.cwd(), 'uploads');
  private screenshotsDir = path.join(process.cwd(), 'debug_screenshots');
  private logsDir = path.join(process.cwd(), 'logs');

  constructor() {
    this.ensureDirectories();
  }

  private ensureDirectories() {
    [this.uploadsDir, this.screenshotsDir, this.logsDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async saveDocument(file: any, type: 'cv' | 'cover-letter'): Promise<string> {
    const extension = path.extname(file.originalname);
    const filename = `${type}_${Date.now()}${extension}`;
    const filepath = path.join(this.uploadsDir, filename);

    await fs.promises.copyFile(file.path, filepath);
    await fs.promises.unlink(file.path); // Clean up temporary file

    return filepath;
  }

  async exportLogs(logs: AutomationLog[]): Promise<string> {
    const exportData = {
      exportDate: new Date().toISOString(),
      totalLogs: logs.length,
      logs: logs.map(log => ({
        timestamp: log.timestamp,
        level: log.level,
        message: log.message,
        metadata: log.metadata,
      })),
    };

    return JSON.stringify(exportData, null, 2);
  }

  async getScreenshotPath(filename: string): Promise<string> {
    return path.join(this.screenshotsDir, filename);
  }

  async fileExists(filepath: string): Promise<boolean> {
    try {
      await fs.promises.access(filepath);
      return true;
    } catch {
      return false;
    }
  }

  async deleteFile(filepath: string): Promise<void> {
    try {
      await fs.promises.unlink(filepath);
    } catch (error) {
      // File might not exist, ignore error
    }
  }

  async getFileSize(filepath: string): Promise<number> {
    try {
      const stats = await fs.promises.stat(filepath);
      return stats.size;
    } catch {
      return 0;
    }
  }
}

export const fileService = new FileService();

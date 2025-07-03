import { pgTable, text, serial, integer, boolean, timestamp, json } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const userConfigs = pgTable("user_configs", {
  id: serial("id").primaryKey(),
  firstName: text("first_name").notNull(),
  lastName: text("last_name").notNull(),
  email: text("email").notNull(),
  phone: text("phone").notNull(),
  message: text("message").notNull(),
  cvPath: text("cv_path"),
  coverLetterPath: text("cover_letter_path"),
  // Search preferences
  searchKeywords: text("search_keywords"), // "développeur web, react, javascript"
  searchLocation: text("search_location"), // "Paris, Lyon, Marseille"
  jobTypes: text("job_types"), // "alternance, stage, apprentissage"
  contractTypes: text("contract_types"), // "CDI, CDD, alternance"
  educationLevel: text("education_level"), // "cap", "bac", "bts", "licence", "master", ""
  searchRadius: text("search_radius"), // "10", "20", "30", "50", "100", "france"
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const automationSessions = pgTable("automation_sessions", {
  id: serial("id").primaryKey(),
  status: text("status").notNull(), // 'running', 'paused', 'stopped', 'completed'
  startedAt: timestamp("started_at").defaultNow(),
  endedAt: timestamp("ended_at"),
  totalApplications: integer("total_applications").default(0),
  successfulApplications: integer("successful_applications").default(0),
  failedApplications: integer("failed_applications").default(0),
  userConfigId: integer("user_config_id").references(() => userConfigs.id),
  settings: json("settings"), // automation settings
});

export const applications = pgTable("applications", {
  id: serial("id").primaryKey(),
  sessionId: integer("session_id").references(() => automationSessions.id),
  jobTitle: text("job_title").notNull(),
  company: text("company").notNull(),
  location: text("location").notNull(),
  status: text("status").notNull(), // 'pending', 'sent', 'failed', 'retrying'
  errorMessage: text("error_message"),
  appliedAt: timestamp("applied_at").defaultNow(),
  screenshotPath: text("screenshot_path"),
  logPath: text("log_path"),
});

export const automationLogs = pgTable("automation_logs", {
  id: serial("id").primaryKey(),
  sessionId: integer("session_id").references(() => automationSessions.id),
  level: text("level").notNull(), // 'info', 'warn', 'error', 'debug', 'success'
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
  metadata: json("metadata"), // additional context
});

export const screenshots = pgTable("screenshots", {
  id: serial("id").primaryKey(),
  sessionId: integer("session_id").references(() => automationSessions.id),
  applicationId: integer("application_id").references(() => applications.id),
  filePath: text("file_path").notNull(),
  description: text("description"),
  capturedAt: timestamp("captured_at").defaultNow(),
});

export const automationSettings = pgTable("automation_settings", {
  id: serial("id").primaryKey(),
  delayBetweenApplications: integer("delay_between_applications").default(30),
  maxApplicationsPerSession: integer("max_applications_per_session").default(50),
  autoFillForm: boolean("auto_fill_form").default(true),
  autoSendApplication: boolean("auto_send_application").default(true),
  pauseBeforeSend: boolean("pause_before_send").default(false),
  captureScreenshots: boolean("capture_screenshots").default(true),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

// Insert schemas
export const insertUserConfigSchema = createInsertSchema(userConfigs).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertAutomationSessionSchema = createInsertSchema(automationSessions).omit({
  id: true,
  startedAt: true,
  endedAt: true,
});

export const insertApplicationSchema = createInsertSchema(applications).omit({
  id: true,
  appliedAt: true,
});

export const insertAutomationLogSchema = createInsertSchema(automationLogs).omit({
  id: true,
  timestamp: true,
});

export const insertScreenshotSchema = createInsertSchema(screenshots).omit({
  id: true,
  capturedAt: true,
});

export const insertAutomationSettingsSchema = createInsertSchema(automationSettings).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

// Types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserConfigSchema>;

export type UserConfig = typeof userConfigs.$inferSelect;
export type InsertUserConfig = z.infer<typeof insertUserConfigSchema>;

export type AutomationSession = typeof automationSessions.$inferSelect;
export type InsertAutomationSession = z.infer<typeof insertAutomationSessionSchema>;

export type Application = typeof applications.$inferSelect;
export type InsertApplication = z.infer<typeof insertApplicationSchema>;

export type AutomationLog = typeof automationLogs.$inferSelect;
export type InsertAutomationLog = z.infer<typeof insertAutomationLogSchema>;

export type Screenshot = typeof screenshots.$inferSelect;
export type InsertScreenshot = z.infer<typeof insertScreenshotSchema>;

export type AutomationSettings = typeof automationSettings.$inferSelect;
export type InsertAutomationSettings = z.infer<typeof insertAutomationSettingsSchema>;

import { useQuery } from "@tanstack/react-query";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAutomation } from "@/hooks/useAutomation";
import ControlPanel from "@/components/ControlPanel";
import UserConfiguration from "@/components/UserConfiguration";
import DocumentManagement from "@/components/DocumentManagement";
import ActivityFeed from "@/components/ActivityFeed";
import ScreenshotGallery from "@/components/ScreenshotGallery";
import LogsViewer from "@/components/LogsViewer";
import ApplicationHistory from "@/components/ApplicationHistory";
import SettingsModal from "@/components/SettingsModal";
import { Button } from "@/components/ui/button";
import { Settings, Bot } from "lucide-react";
import { useState } from "react";

export default function Dashboard() {
  const [showSettings, setShowSettings] = useState(false);
  const { status, isLoading: statusLoading } = useAutomation();
  const { data: userConfig } = useQuery({
    queryKey: ['/api/user-config'],
  });

  useWebSocket();

  const isRunning = (status as any)?.isRunning || false;
  const statistics = (status as any)?.statistics || {
    totalApplications: 0,
    successfulApplications: 0,
    failedApplications: 0,
    elapsedTime: 0,
  };

  const formatElapsedTime = (milliseconds: number) => {
    const hours = Math.floor(milliseconds / (1000 * 60 * 60));
    const minutes = Math.floor((milliseconds % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Bot className="text-primary text-2xl mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Alternance Auto-Postulation</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isRunning ? 'En cours' : 'Arrêté'}
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(true)}
                className="flex items-center space-x-2"
              >
                <Settings className="w-4 h-4" />
                <span>Paramètres</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Control Panel */}
        <ControlPanel
          isRunning={isRunning}
          statistics={statistics}
          elapsedTime={formatElapsedTime(statistics.elapsedTime)}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Configuration */}
          <div className="lg:col-span-1 space-y-6">
            <UserConfiguration userConfig={userConfig} />
            <DocumentManagement userConfig={userConfig} />
          </div>

          {/* Right Column - Activity & Monitoring */}
          <div className="lg:col-span-2 space-y-6">
            <ActivityFeed />
            <ScreenshotGallery />
            <LogsViewer />
          </div>
        </div>

        {/* Application History */}
        <ApplicationHistory />
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  );
}

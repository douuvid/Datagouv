import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Play, Pause, Square, Send, CheckCircle, XCircle, Clock } from "lucide-react";
import { useAutomation } from "@/hooks/useAutomation";

interface ControlPanelProps {
  isRunning: boolean;
  statistics: {
    totalApplications: number;
    successfulApplications: number;
    failedApplications: number;
    elapsedTime: number;
  };
  elapsedTime: string;
}

export default function ControlPanel({ isRunning, statistics, elapsedTime }: ControlPanelProps) {
  const { startAutomation, pauseAutomation, stopAutomation, isLoading } = useAutomation();

  const progressPercentage = statistics.totalApplications > 0 
    ? (statistics.successfulApplications / statistics.totalApplications) * 100 
    : 0;

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Contrôle des Postulations
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Control Buttons */}
          <div className="space-y-3">
            <Button
              onClick={startAutomation}
              disabled={isRunning || isLoading}
              className="w-full bg-secondary hover:bg-secondary/90 text-white"
            >
              <Play className="w-4 h-4 mr-2" />
              Démarrer
            </Button>
            <Button
              onClick={pauseAutomation}
              disabled={!isRunning || isLoading}
              variant="outline"
              className="w-full border-amber-500 text-amber-600 hover:bg-amber-50"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
            <Button
              onClick={stopAutomation}
              disabled={!isRunning || isLoading}
              variant="destructive"
              className="w-full"
            >
              <Square className="w-4 h-4 mr-2" />
              Arrêter
            </Button>
          </div>

          {/* Statistics Cards */}
          <div className="space-y-3">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Send className="text-primary mr-3" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Postulations envoyées</p>
                  <p className="text-2xl font-bold text-primary">{statistics.totalApplications}</p>
                </div>
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="text-secondary mr-3" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Succès</p>
                  <p className="text-2xl font-bold text-secondary">{statistics.successfulApplications}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center">
                <XCircle className="text-destructive mr-3" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Échecs</p>
                  <p className="text-2xl font-bold text-destructive">{statistics.failedApplications}</p>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Clock className="text-accent mr-3" size={20} />
                <div>
                  <p className="text-sm text-gray-600">Temps écoulé</p>
                  <p className="text-lg font-bold text-accent">{elapsedTime}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">Progression du processus</span>
            <span className="text-sm text-gray-600">{Math.round(progressPercentage)}%</span>
          </div>
          <Progress value={progressPercentage} className="w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { Loader2, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

export default function ActivityFeed() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['/api/logs'],
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const recentLogs = Array.isArray(logs) ? logs.slice(0, 10) : [];

  const getIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="text-green-500" size={16} />;
      case 'error':
        return <XCircle className="text-red-500" size={16} />;
      case 'warn':
        return <AlertTriangle className="text-yellow-500" size={16} />;
      case 'info':
      default:
        return <Loader2 className="text-blue-500 animate-spin" size={16} />;
    }
  };

  const getBgColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'bg-green-50';
      case 'error':
        return 'bg-red-50';
      case 'warn':
        return 'bg-yellow-50';
      case 'info':
      default:
        return 'bg-gray-50';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Activité en Temps Réel
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="animate-spin mr-2" />
              <span>Chargement des activités...</span>
            </div>
          ) : recentLogs.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              Aucune activité récente
            </p>
          ) : (
            recentLogs.map((log: any) => (
              <div key={log.id} className={`flex items-start space-x-3 p-4 rounded-lg ${getBgColor(log.level)}`}>
                <div className="flex-shrink-0">
                  {getIcon(log.level)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {log.message}
                  </p>
                  <p className="text-xs text-gray-500">
                    {format(new Date(log.timestamp), 'PPpp', { locale: fr })}
                  </p>
                  {log.metadata && (
                    <p className="text-xs text-gray-600 mt-1">
                      {JSON.stringify(log.metadata)}
                    </p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

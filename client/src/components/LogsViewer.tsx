import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/api";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Trash2 } from "lucide-react";
import { format } from "date-fns";

export default function LogsViewer() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: logs, isLoading } = useQuery({
    queryKey: ['/api/logs'],
    refetchInterval: 5000,
  });

  const clearLogsMutation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('DELETE', '/api/logs');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Logs effacés",
        description: "Les logs ont été effacés avec succès.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/logs'] });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible d'effacer les logs.",
        variant: "destructive",
      });
    },
  });

  const exportLogsMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/logs/export');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'automation_logs.json';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
    onSuccess: () => {
      toast({
        title: "Export réussi",
        description: "Les logs ont été exportés avec succès.",
      });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible d'exporter les logs.",
        variant: "destructive",
      });
    },
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      case 'warn':
        return 'text-yellow-400';
      case 'debug':
        return 'text-purple-400';
      case 'info':
      default:
        return 'text-blue-400';
    }
  };

  const formatLogEntry = (log: any) => {
    const timestamp = format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss');
    const level = log.level.toUpperCase();
    return `[${timestamp}] ${level} ${log.message}`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg font-semibold text-gray-900">
            Logs Détaillés
          </CardTitle>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => clearLogsMutation.mutate()}
              disabled={clearLogsMutation.isPending}
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Effacer
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => exportLogsMutation.mutate()}
              disabled={exportLogsMutation.isPending}
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="text-center py-4">
              <span className="text-gray-500">Chargement des logs...</span>
            </div>
          ) : !logs || !Array.isArray(logs) || logs.length === 0 ? (
            <div className="text-center py-4">
              <span className="text-gray-500">Aucun log disponible</span>
            </div>
          ) : (
            Array.isArray(logs) && logs.map((log: any) => (
              <div key={log.id} className="mb-1">
                <span className="text-gray-500">{format(new Date(log.timestamp), 'yyyy-MM-dd HH:mm:ss')}</span>
                <span className={`ml-2 ${getLevelColor(log.level)}`}>{log.level.toUpperCase()}</span>
                <span className="ml-2">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

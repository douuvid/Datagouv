import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';
import { apiRequest } from '@/lib/api';

export function useAutomation() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: status, isLoading } = useQuery({
    queryKey: ['/api/automation/status'],
    refetchInterval: 5000,
  });

  const startAutomation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/api/automation/start');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Automatisation démarrée",
        description: "Le processus de postulation automatique a été démarré.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
    },
    onError: (error: any) => {
      toast({
        title: "Erreur",
        description: error.message || "Impossible de démarrer l'automatisation.",
        variant: "destructive",
      });
    },
  });

  const pauseAutomation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/api/automation/pause');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Automatisation en pause",
        description: "Le processus de postulation automatique a été mis en pause.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
    },
    onError: (error: any) => {
      toast({
        title: "Erreur",
        description: error.message || "Impossible de mettre en pause l'automatisation.",
        variant: "destructive",
      });
    },
  });

  const stopAutomation = useMutation({
    mutationFn: async () => {
      const response = await apiRequest('POST', '/api/automation/stop');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Automatisation arrêtée",
        description: "Le processus de postulation automatique a été arrêté.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
    },
    onError: (error: any) => {
      toast({
        title: "Erreur",
        description: error.message || "Impossible d'arrêter l'automatisation.",
        variant: "destructive",
      });
    },
  });

  return {
    status,
    isLoading: isLoading || startAutomation.isPending || pauseAutomation.isPending || stopAutomation.isPending,
    startAutomation: () => startAutomation.mutate(),
    pauseAutomation: () => pauseAutomation.mutate(),
    stopAutomation: () => stopAutomation.mutate(),
  };
}

import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/hooks/use-toast';

export function useWebSocket() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        handleReconnect();
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      handleReconnect();
    }
  };

  const handleReconnect = () => {
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }

    reconnectAttempts.current++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Reconnecting... (attempt ${reconnectAttempts.current})`);
      connect();
    }, delay);
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'session_started':
        toast({
          title: "Automatisation démarrée",
          description: "Le processus de postulation automatique a été démarré.",
        });
        queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
        break;

      case 'session_paused':
        toast({
          title: "Automatisation en pause",
          description: "Le processus de postulation automatique a été mis en pause.",
        });
        queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
        break;

      case 'session_stopped':
        toast({
          title: "Automatisation arrêtée",
          description: "Le processus de postulation automatique a été arrêté.",
        });
        queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
        break;

      case 'session_ended':
        toast({
          title: "Automatisation terminée",
          description: "Le processus de postulation automatique s'est terminé avec succès.",
        });
        queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
        queryClient.invalidateQueries({ queryKey: ['/api/applications'] });
        break;

      case 'application_started':
        queryClient.invalidateQueries({ queryKey: ['/api/applications'] });
        break;

      case 'application_updated':
        queryClient.invalidateQueries({ queryKey: ['/api/applications'] });
        if (data.data.status === 'sent') {
          toast({
            title: "Candidature envoyée",
            description: `Candidature pour "${data.data.jobTitle}" envoyée avec succès.`,
          });
        } else if (data.data.status === 'failed') {
          toast({
            title: "Échec de candidature",
            description: `Échec pour "${data.data.jobTitle}": ${data.data.errorMessage}`,
            variant: "destructive",
          });
        }
        break;

      case 'screenshot_captured':
        queryClient.invalidateQueries({ queryKey: ['/api/screenshots'] });
        break;

      case 'session_stats_updated':
        queryClient.invalidateQueries({ queryKey: ['/api/automation/status'] });
        break;

      case 'log_created':
        queryClient.invalidateQueries({ queryKey: ['/api/logs'] });
        break;

      case 'automation_error':
        toast({
          title: "Erreur d'automatisation",
          description: data.data.error,
          variant: "destructive",
        });
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
  };
}

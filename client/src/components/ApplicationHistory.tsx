import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { Eye, Download, CheckCircle, XCircle, Clock } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import { useToast } from "@/hooks/use-toast";

export default function ApplicationHistory() {
  const { data: applications = [], isLoading } = useQuery({
    queryKey: ['/api/applications'],
    refetchInterval: 10000,
  });

  const { toast } = useToast();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent':
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            Envoyée
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="bg-red-100 text-red-800">
            <XCircle className="w-3 h-3 mr-1" />
            Échoué
          </Badge>
        );
      case 'pending':
        return (
          <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
            <Clock className="w-3 h-3 mr-1" />
            En cours
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            {status}
          </Badge>
        );
    }
  };

  return (
    <Card className="mt-8">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Historique des Candidatures
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="text-center py-8">
            <span className="text-gray-500">Chargement de l'historique...</span>
          </div>
        ) : !applications || !Array.isArray(applications) || applications.length === 0 ? (
          <div className="text-center py-8">
            <span className="text-gray-500">Aucune candidature trouvée</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Offre</TableHead>
                  <TableHead>Entreprise</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array.isArray(applications) && applications.map((application: any) => (
                  <TableRow key={application.id} className="hover:bg-gray-50">
                    <TableCell className="text-sm text-gray-900">
                      {format(new Date(application.appliedAt), 'PPpp', { locale: fr })}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm font-medium text-gray-900">
                        {application.jobTitle}
                      </div>
                      <div className="text-sm text-gray-500">
                        {application.location}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-900">
                      {application.company}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {getStatusBadge(application.status)}
                        {application.status === 'failed' && application.errorMessage && (
                          <div className="text-xs text-red-600 max-w-xs">
                            {application.errorMessage}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-primary hover:text-primary/80"
                          onClick={() => {
                            toast({
                              title: "Capture d'écran",
                              description: `Affichage de la capture pour ${application.jobTitle}`,
                            });
                            // TODO: Ouvrir modal avec screenshot
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-gray-400 hover:text-gray-600"
                          onClick={() => {
                            const logData = `
CANDIDATURE - ${application.jobTitle}
Entreprise: ${application.company}
Localisation: ${application.location}
Statut: ${application.status}
Date: ${new Date(application.appliedAt).toLocaleString('fr-FR')}
${application.errorMessage ? `Erreur: ${application.errorMessage}` : 'Candidature envoyée avec succès'}
                            `.trim();
                            
                            const blob = new Blob([logData], { type: 'text/plain' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `candidature-${application.company.replace(/\s+/g, '-')}-${application.id}.txt`;
                            a.click();
                            URL.revokeObjectURL(url);
                            
                            toast({
                              title: "Fichier téléchargé",
                              description: `Rapport de candidature pour ${application.company}`,
                            });
                          }}
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

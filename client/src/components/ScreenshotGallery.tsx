import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { useQuery } from "@tanstack/react-query";
import { Expand, Image as ImageIcon } from "lucide-react";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

export default function ScreenshotGallery() {
  const { data: screenshots, isLoading } = useQuery({
    queryKey: ['/api/screenshots'],
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const recentScreenshots = Array.isArray(screenshots) ? screenshots.slice(0, 6) : [];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-gray-900">
            Captures d'Écran de Débogage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="aspect-video bg-gray-200 rounded-lg animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Captures d'Écran de Débogage
        </CardTitle>
      </CardHeader>
      <CardContent>
        {recentScreenshots.length === 0 ? (
          <div className="text-center py-8">
            <ImageIcon className="mx-auto text-gray-400 mb-4" size={48} />
            <p className="text-gray-500">Aucune capture d'écran disponible</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {recentScreenshots.map((screenshot: any) => (
              <Dialog key={screenshot.id}>
                <DialogTrigger asChild>
                  <div className="relative group cursor-pointer">
                    <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
                      <ImageIcon className="text-gray-400" size={24} />
                    </div>
                    <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
                      <Expand className="text-white" size={24} />
                    </div>
                    <div className="absolute bottom-2 left-2 right-2">
                      <p className="text-xs text-white bg-black bg-opacity-70 px-2 py-1 rounded truncate">
                        {screenshot.description || 'Capture d\'écran'}
                      </p>
                    </div>
                  </div>
                </DialogTrigger>
                <DialogContent className="max-w-4xl">
                  <DialogHeader>
                    <DialogTitle>{screenshot.description || 'Capture d\'écran'}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="bg-gray-100 rounded-lg p-4">
                      <p className="text-sm text-gray-600">
                        Capturé le {format(new Date(screenshot.capturedAt), 'PPpp', { locale: fr })}
                      </p>
                    </div>
                    <div className="bg-gray-200 rounded-lg aspect-video flex items-center justify-center">
                      <ImageIcon className="text-gray-400" size={48} />
                      <span className="ml-2 text-gray-600">Aperçu de l'image</span>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

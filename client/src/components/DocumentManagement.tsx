import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Upload, CheckCircle } from "lucide-react";
import { useRef } from "react";

interface DocumentManagementProps {
  userConfig?: any;
}

export default function DocumentManagement({ userConfig }: DocumentManagementProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const cvInputRef = useRef<HTMLInputElement>(null);
  const coverLetterInputRef = useRef<HTMLInputElement>(null);

  const uploadCVMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('cv', file);
      const response = await fetch('/api/upload/cv', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "CV uploadé",
        description: "Votre CV a été uploadé avec succès.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/user-config'] });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible d'uploader le CV.",
        variant: "destructive",
      });
    },
  });

  const uploadCoverLetterMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('coverLetter', file);
      const response = await fetch('/api/upload/cover-letter', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Upload failed');
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Lettre de motivation uploadée",
        description: "Votre lettre de motivation a été uploadée avec succès.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/user-config'] });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible d'uploader la lettre de motivation.",
        variant: "destructive",
      });
    },
  });

  const handleCVUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadCVMutation.mutate(file);
    }
  };

  const handleCoverLetterUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      uploadCoverLetterMutation.mutate(file);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Gestion des Documents
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* CV Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <FileText className="mx-auto text-4xl text-gray-400 mb-4" />
          <p className="text-sm text-gray-600 mb-2">CV (PDF)</p>
          <p className="text-xs text-gray-500 mb-4">
            {userConfig?.cvPath ? "Fichier uploadé" : "Glisser-déposer ou cliquer pour uploader"}
          </p>
          <input
            ref={cvInputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleCVUpload}
            className="hidden"
          />
          <Button
            onClick={() => cvInputRef.current?.click()}
            variant="outline"
            disabled={uploadCVMutation.isPending}
          >
            <Upload className="w-4 h-4 mr-2" />
            {uploadCVMutation.isPending ? "Upload..." : "Choisir un fichier"}
          </Button>
        </div>

        {/* Cover Letter Upload */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <FileText className="mx-auto text-4xl text-gray-400 mb-4" />
          <p className="text-sm text-gray-600 mb-2">Lettre de motivation (PDF)</p>
          <p className="text-xs text-gray-500 mb-4">
            {userConfig?.coverLetterPath ? "Fichier uploadé" : "Glisser-déposer ou cliquer pour uploader"}
          </p>
          <input
            ref={coverLetterInputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleCoverLetterUpload}
            className="hidden"
          />
          <Button
            onClick={() => coverLetterInputRef.current?.click()}
            variant="outline"
            disabled={uploadCoverLetterMutation.isPending}
          >
            <Upload className="w-4 h-4 mr-2" />
            {uploadCoverLetterMutation.isPending ? "Upload..." : "Choisir un fichier"}
          </Button>
        </div>

        {/* Status */}
        {userConfig?.cvPath && userConfig?.coverLetterPath && (
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <CheckCircle className="text-secondary mr-3" size={20} />
              <div>
                <p className="text-sm font-medium text-secondary">Documents configurés</p>
                <p className="text-xs text-gray-600">CV et lettre de motivation prêts</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

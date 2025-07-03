import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/api";
import { insertUserConfigSchema } from "@shared/schema";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Save } from "lucide-react";

const formSchema = insertUserConfigSchema.extend({
  firstName: z.string().min(1, "Le prénom est requis"),
  lastName: z.string().min(1, "Le nom est requis"),
  email: z.string().email("Email invalide"),
  phone: z.string().min(10, "Numéro de téléphone invalide"),
  message: z.string().min(10, "Le message doit contenir au moins 10 caractères"),
});

interface UserConfigurationProps {
  userConfig?: any;
}

export default function UserConfiguration({ userConfig }: UserConfigurationProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      firstName: userConfig?.firstName || "",
      lastName: userConfig?.lastName || "",
      email: userConfig?.email || "",
      phone: userConfig?.phone || "",
      message: userConfig?.message || `Bonjour,

Je suis vivement intéressé(e) par cette offre d'alternance qui correspond parfaitement à mon projet professionnel. 
Mon profil et ma formation correspondent aux compétences requises pour ce poste.

Je serais ravi(e) de pouvoir échanger avec vous pour vous présenter ma motivation et mes ambitions.

Cordialement,
[Prénom Nom]`,
    },
  });

  const saveConfigMutation = useMutation({
    mutationFn: async (data: z.infer<typeof formSchema>) => {
      const response = await apiRequest('POST', '/api/user-config', data);
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Configuration sauvegardée",
        description: "Vos données utilisateur ont été enregistrées avec succès.",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/user-config'] });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder la configuration.",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: z.infer<typeof formSchema>) => {
    saveConfigMutation.mutate(data);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-gray-900">
          Configuration Utilisateur
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="firstName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Prénom</FormLabel>
                  <FormControl>
                    <Input placeholder="Jean" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="lastName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nom</FormLabel>
                  <FormControl>
                    <Input placeholder="Dupont" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="jean.dupont@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Téléphone</FormLabel>
                  <FormControl>
                    <Input type="tel" placeholder="06 12 34 56 78" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="message"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Message de candidature</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={6}
                      placeholder="Votre message de candidature..."
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="border-t pt-4">
              <h3 className="text-md font-semibold mb-3">Préférences de recherche</h3>
              
              <FormField
                control={form.control}
                name="searchKeywords"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mots-clés de recherche</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="développeur web, react, javascript, full stack" 
                        {...field}
                        value={field.value || ''}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="searchLocation"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Localisation préférée</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="Paris, Lyon, Marseille, télétravail" 
                        {...field}
                        value={field.value || ''}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="jobTypes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Types de contrat</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="alternance, stage, apprentissage" 
                        {...field}
                        value={field.value || ''}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="experienceLevel"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Niveau d'expérience</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="junior, débutant, 1-2 ans d'expérience" 
                        {...field}
                        value={field.value || ''}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={saveConfigMutation.isPending}
            >
              <Save className="w-4 h-4 mr-2" />
              {saveConfigMutation.isPending ? "Enregistrement..." : "Enregistrer"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

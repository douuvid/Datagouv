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
  searchKeywords: z.string().optional(),
  searchLocation: z.string().optional(),
  educationLevel: z.string().optional(),
  searchRadius: z.string().optional(),
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
      searchKeywords: userConfig?.searchKeywords || "",
      searchLocation: userConfig?.searchLocation || "",
      educationLevel: userConfig?.educationLevel || "",
      searchRadius: userConfig?.searchRadius || "",
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



              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="educationLevel"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Niveau de formation</FormLabel>
                      <FormControl>
                        <select 
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          {...field}
                          value={field.value || ''}
                        >
                          <option value="">~ Indifférent</option>
                          <option value="cap">Cap, autres formations niveau 3</option>
                          <option value="bac">Bac, autres formations niveau 4</option>
                          <option value="bts">BTS, DEUST, autres formations niveaux 5 (Bac+2)</option>
                          <option value="licence">Licence, Maîtrise, autres formations niveaux 6 (Bac+3 à Bac+4)</option>
                          <option value="master">Master, titre ingénieur, autres formations niveaux 7 ou 8 (Bac+5)</option>
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="searchRadius"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rayon de recherche</FormLabel>
                      <FormControl>
                        <select 
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          {...field}
                          value={field.value || ''}
                        >
                          <option value="10">10 km</option>
                          <option value="20">20 km</option>
                          <option value="30">30 km</option>
                          <option value="50">50 km</option>
                          <option value="100">100 km</option>
                          <option value="france">Toute la France</option>
                        </select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
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

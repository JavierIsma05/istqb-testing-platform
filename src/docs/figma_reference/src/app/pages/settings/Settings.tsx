import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Label } from "../../components/ui/label";
import { Switch } from "../../components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Save, Bell, Palette, Globe, Shield } from "lucide-react";
import { toast } from "sonner";

export default function Settings() {
  const handleSave = () => toast.success("Configuración guardada exitosamente");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Configuración</h1>
        <p className="text-muted-foreground">Personaliza la plataforma según tus preferencias</p>
      </div>

      <Tabs defaultValue="general" className="space-y-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="notifications">Notificaciones</TabsTrigger>
          <TabsTrigger value="appearance">Apariencia</TabsTrigger>
          <TabsTrigger value="privacy">Privacidad</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Configuración General</CardTitle>
              <CardDescription>Preferencias básicas de la plataforma</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Idioma</Label>
                <Select defaultValue="es">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Zona Horaria</Label>
                <Select defaultValue="ec">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ec">Ecuador (GMT-5)</SelectItem>
                    <SelectItem value="co">Colombia (GMT-5)</SelectItem>
                    <SelectItem value="pe">Perú (GMT-5)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                Guardar Cambios
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Preferencias de Notificaciones</CardTitle>
              <CardDescription>Gestiona cómo y cuándo recibes notificaciones</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Notificaciones por Email</Label>
                  <p className="text-sm text-muted-foreground">Recibe actualizaciones por correo electrónico</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Nuevos Defectos</Label>
                  <p className="text-sm text-muted-foreground">Notificar cuando se registren defectos</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Mensajes del Tutor</Label>
                  <p className="text-sm text-muted-foreground">Alertas de mensajes de tutores</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Recordatorios de Fechas</Label>
                  <p className="text-sm text-muted-foreground">Avisos sobre fechas límite</p>
                </div>
                <Switch defaultChecked />
              </div>
              <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                <Bell className="w-4 h-4 mr-2" />
                Guardar Preferencias
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Apariencia</CardTitle>
              <CardDescription>Personaliza la interfaz de la plataforma</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Tema</Label>
                <Select defaultValue="light">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Claro</SelectItem>
                    <SelectItem value="dark">Oscuro</SelectItem>
                    <SelectItem value="auto">Automático</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Modo Compacto</Label>
                  <p className="text-sm text-muted-foreground">Reduce el espaciado en la interfaz</p>
                </div>
                <Switch />
              </div>
              <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                <Palette className="w-4 h-4 mr-2" />
                Aplicar Cambios
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="privacy" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Privacidad y Seguridad</CardTitle>
              <CardDescription>Controla tu privacidad y seguridad</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Perfil Público</Label>
                  <p className="text-sm text-muted-foreground">Permite que otros vean tu perfil</p>
                </div>
                <Switch />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Autenticación de Dos Factores</Label>
                  <p className="text-sm text-muted-foreground">Añade una capa extra de seguridad</p>
                </div>
                <Switch />
              </div>
              <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                <Shield className="w-4 h-4 mr-2" />
                Guardar Configuración
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

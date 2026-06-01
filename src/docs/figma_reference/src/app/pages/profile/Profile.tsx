import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { Badge } from "../../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { User, Mail, Building2, Calendar, Save, Shield } from "lucide-react";
import { toast } from "sonner";

export default function Profile() {
  const handleSave = () => toast.success("Perfil actualizado exitosamente");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Mi Perfil</h1>
        <p className="text-muted-foreground">Administra tu información personal</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center text-center space-y-4">
              <Avatar className="w-24 h-24">
                <AvatarFallback className="bg-[#4B6B88] text-white text-2xl">JP</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lg">Juan Pérez García</h3>
                <p className="text-sm text-muted-foreground">estudiante@uni.edu</p>
              </div>
              <Badge className="bg-[#E0F2FE] text-[#4B6B88]">Estudiante</Badge>
              <div className="w-full space-y-2 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Building2 className="w-4 h-4" />
                  <span>Universidad Técnica</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="w-4 h-4" />
                  <span>Miembro desde Mar 2026</span>
                </div>
              </div>
              <Button variant="outline" className="w-full">Cambiar Foto</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Información del Perfil</CardTitle>
            <CardDescription>Actualiza tus datos personales</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="personal">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="personal">Datos Personales</TabsTrigger>
                <TabsTrigger value="security">Seguridad</TabsTrigger>
              </TabsList>

              <TabsContent value="personal" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nombre</Label>
                    <Input defaultValue="Juan" />
                  </div>
                  <div className="space-y-2">
                    <Label>Apellidos</Label>
                    <Input defaultValue="Pérez García" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" defaultValue="estudiante@uni.edu" />
                </div>
                <div className="space-y-2">
                  <Label>Institución</Label>
                  <Input defaultValue="Universidad Técnica" />
                </div>
                <div className="space-y-2">
                  <Label>Teléfono</Label>
                  <Input defaultValue="+593 99 123 4567" />
                </div>
                <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                  <Save className="w-4 h-4 mr-2" />
                  Guardar Cambios
                </Button>
              </TabsContent>

              <TabsContent value="security" className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Contraseña Actual</Label>
                  <Input type="password" placeholder="••••••••" />
                </div>
                <div className="space-y-2">
                  <Label>Nueva Contraseña</Label>
                  <Input type="password" placeholder="••••••••" />
                </div>
                <div className="space-y-2">
                  <Label>Confirmar Nueva Contraseña</Label>
                  <Input type="password" placeholder="••••••••" />
                </div>
                <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleSave}>
                  <Shield className="w-4 h-4 mr-2" />
                  Actualizar Contraseña
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actividad Reciente</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#22C55E]"></div>
              <span className="text-muted-foreground">Ejecutó caso de prueba TC-045</span>
              <span className="text-xs text-muted-foreground ml-auto">Hace 2 horas</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#4B6B88]"></div>
              <span className="text-muted-foreground">Actualizó plan de pruebas v2.1</span>
              <span className="text-xs text-muted-foreground ml-auto">Hace 1 día</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#EF4444]"></div>
              <span className="text-muted-foreground">Registró defecto DEF-023</span>
              <span className="text-xs text-muted-foreground ml-auto">Hace 2 días</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

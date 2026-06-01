import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Users, Shield, Activity, Settings, Plus, MoreVertical } from "lucide-react";
import { Avatar, AvatarFallback } from "../../components/ui/avatar";

export default function AdminPanel() {
  const users = [
    { name: "Juan Pérez", email: "juan@uni.edu", role: "Estudiante", status: "Activo", projects: 2 },
    { name: "María García", email: "maria@uni.edu", role: "Estudiante", status: "Activo", projects: 1 },
    { name: "Dr. González", email: "gonzalez@uni.edu", role: "Tutor", status: "Activo", projects: 8 },
    { name: "Admin User", email: "admin@uni.edu", role: "Admin", status: "Activo", projects: 0 },
  ];

  const logs = [
    { user: "Juan Pérez", action: "Creó caso de prueba TC-045", time: "Hace 1 hora", type: "create" },
    { user: "Dr. González", action: "Aprobó plan de pruebas v2.1", time: "Hace 2 horas", type: "approve" },
    { user: "María García", action: "Registró defecto DEF-024", time: "Hace 3 horas", type: "report" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Panel de Administración</h1>
          <p className="text-muted-foreground">Gestión global de la plataforma</p>
        </div>
        <Badge className="bg-[#EF4444] text-white">Admin Only</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Usuarios</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">156</p>
              </div>
              <Users className="w-8 h-8 text-[#4B6B88]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Tutores</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">24</p>
              </div>
              <Shield className="w-8 h-8 text-[#22C55E]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Estudiantes</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">108</p>
              </div>
              <Users className="w-8 h-8 text-[#7DD3FC]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Sesiones Activas</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">42</p>
              </div>
              <Activity className="w-8 h-8 text-[#FACC15]" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users">Usuarios</TabsTrigger>
          <TabsTrigger value="logs">Auditoría</TabsTrigger>
          <TabsTrigger value="settings">Configuración</TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Gestión de Usuarios</CardTitle>
                  <CardDescription>Administra usuarios y sus roles</CardDescription>
                </div>
                <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
                  <Plus className="w-4 h-4 mr-2" />
                  Nuevo Usuario
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {users.map((user, index) => (
                  <div key={index} className="p-4 border rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Avatar>
                        <AvatarFallback className="bg-[#4B6B88] text-white">
                          {user.name.split(' ').map(n => n[0]).join('')}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <h3 className="font-semibold text-[#1E3A5F]">{user.name}</h3>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={
                        user.role === "Admin" ? "bg-[#EF4444] text-white" :
                        user.role === "Tutor" ? "bg-[#4B6B88] text-white" :
                        "bg-[#E0F2FE] text-[#4B6B88]"
                      }>
                        {user.role}
                      </Badge>
                      <Badge variant="outline">{user.projects} proyectos</Badge>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Registro de Auditoría</CardTitle>
              <CardDescription>Historial de actividad de la plataforma</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-3 pb-3 border-b last:border-0">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      log.type === 'create' ? 'bg-[#22C55E]' :
                      log.type === 'approve' ? 'bg-[#4B6B88]' : 'bg-[#EF4444]'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm"><span className="font-semibold">{log.user}</span> {log.action}</p>
                      <p className="text-xs text-muted-foreground mt-1">{log.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Configuración del Sistema</CardTitle>
              <CardDescription>Configuración global de la plataforma</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-[#1E3A5F]">Modo de Mantenimiento</h3>
                      <p className="text-sm text-muted-foreground">Deshabilitar acceso a usuarios</p>
                    </div>
                    <Button variant="outline">Configurar</Button>
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-[#1E3A5F]">Copias de Seguridad</h3>
                      <p className="text-sm text-muted-foreground">Gestionar backups automáticos</p>
                    </div>
                    <Button variant="outline">Ver Backups</Button>
                  </div>
                </div>
                <div className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-[#1E3A5F]">Logs del Sistema</h3>
                      <p className="text-sm text-muted-foreground">Revisar logs de errores</p>
                    </div>
                    <Button variant="outline">Ver Logs</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

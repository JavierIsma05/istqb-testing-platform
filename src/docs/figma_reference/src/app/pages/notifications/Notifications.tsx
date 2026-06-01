import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Bell, CheckCircle2, AlertTriangle, MessageSquare, FileText, Trash2 } from "lucide-react";

export default function Notifications() {
  const notifications = [
    {
      id: 1,
      type: "defect",
      title: "Nuevo defecto registrado",
      message: "Se ha reportado DEF-023 en el módulo de login",
      time: "Hace 2 horas",
      read: false,
      icon: AlertTriangle,
      color: "text-[#EF4444]"
    },
    {
      id: 2,
      type: "test",
      title: "Casos de prueba actualizados",
      message: "El tutor ha revisado TC-045 con observaciones",
      time: "Hace 4 horas",
      read: false,
      icon: FileText,
      color: "text-[#4B6B88]"
    },
    {
      id: 3,
      type: "message",
      title: "Mensaje del tutor",
      message: "Dr. González: 'Por favor revisa los requisitos actualizados'",
      time: "Hace 1 día",
      read: true,
      icon: MessageSquare,
      color: "text-[#7DD3FC]"
    },
    {
      id: 4,
      type: "success",
      title: "Cobertura actualizada",
      message: "La cobertura del proyecto alcanzó 87%",
      time: "Hace 2 días",
      read: true,
      icon: CheckCircle2,
      color: "text-[#22C55E]"
    },
  ];

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Notificaciones</h1>
          <p className="text-muted-foreground">Centro de notificaciones y mensajes</p>
        </div>
        {unreadCount > 0 && (
          <Badge className="bg-[#EF4444] text-white">
            {unreadCount} nuevas
          </Badge>
        )}
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">Todas ({notifications.length})</TabsTrigger>
          <TabsTrigger value="unread">No leídas ({unreadCount})</TabsTrigger>
          <TabsTrigger value="read">Leídas ({notifications.length - unreadCount})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-3">
          {notifications.map((notification) => {
            const Icon = notification.icon;
            return (
              <Card key={notification.id} className={!notification.read ? "border-l-4 border-l-[#4B6B88]" : ""}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg bg-${notification.color.replace('text-', '')}/10`}>
                      <Icon className={`w-5 h-5 ${notification.color}`} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-1">
                        <h3 className="font-semibold text-[#1E3A5F]">{notification.title}</h3>
                        <span className="text-xs text-muted-foreground">{notification.time}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">{notification.message}</p>
                      <div className="flex gap-2">
                        {!notification.read && (
                          <Button variant="outline" size="sm">
                            Marcar como leída
                          </Button>
                        )}
                        <Button variant="ghost" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="unread" className="space-y-3">
          {notifications.filter(n => !n.read).map((notification) => {
            const Icon = notification.icon;
            return (
              <Card key={notification.id} className="border-l-4 border-l-[#4B6B88]">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg bg-${notification.color.replace('text-', '')}/10`}>
                      <Icon className={`w-5 h-5 ${notification.color}`} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-[#1E3A5F] mb-1">{notification.title}</h3>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="read" className="space-y-3">
          {notifications.filter(n => n.read).map((notification) => {
            const Icon = notification.icon;
            return (
              <Card key={notification.id}>
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <Icon className={`w-5 h-5 ${notification.color}`} />
                    <div className="flex-1">
                      <h3 className="font-semibold text-[#1E3A5F] mb-1">{notification.title}</h3>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>
      </Tabs>
    </div>
  );
}

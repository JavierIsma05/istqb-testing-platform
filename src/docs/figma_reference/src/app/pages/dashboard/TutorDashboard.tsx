import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { Users, FolderKanban, CheckCircle2, AlertTriangle, MessageSquare, Calendar } from "lucide-react";
import { Progress } from "../../components/ui/progress";

export default function TutorDashboard() {
  const stats = [
    { title: "Estudiantes Asignados", value: "8", icon: Users, color: "text-[#4B6B88]", bgColor: "bg-[#E0F2FE]" },
    { title: "Proyectos Activos", value: "8", icon: FolderKanban, color: "text-[#22C55E]", bgColor: "bg-green-100" },
    { title: "Revisiones Pendientes", value: "3", icon: AlertTriangle, color: "text-[#FACC15]", bgColor: "bg-yellow-100" },
    { title: "Proyectos Finalizados", value: "12", icon: CheckCircle2, color: "text-[#7DD3FC]", bgColor: "bg-blue-100" },
  ];

  const students = [
    { name: "Juan Pérez", project: "Sistema Académico", progress: 65, status: "En ejecución", pending: "2 casos de prueba" },
    { name: "María García", project: "App Biblioteca", progress: 40, status: "En diseño", pending: "Plan de pruebas" },
    { name: "Carlos Ruiz", project: "Control Inventario", progress: 85, status: "En revisión", pending: "Informe final" },
    { name: "Ana Silva", project: "Portal Servicios", progress: 28, status: "Planificación", pending: "Requisitos" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F] mb-2">Dashboard Tutor</h1>
        <p className="text-muted-foreground">Gestiona y supervisa los proyectos de tus estudiantes</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
                <div className={`${stat.bgColor} p-2 rounded-lg`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-[#1E3A5F]">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Estudiantes y Proyectos</CardTitle>
          <CardDescription>Estado de los proyectos asignados</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {students.map((student, index) => (
            <div key={index} className="p-4 border rounded-lg space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback className="bg-[#4B6B88] text-white">
                      {student.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h3 className="font-semibold text-[#1E3A5F]">{student.name}</h3>
                    <p className="text-sm text-muted-foreground">{student.project}</p>
                  </div>
                </div>
                <Badge className="bg-[#E0F2FE] text-[#4B6B88]">{student.status}</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progreso</span>
                  <span className="font-semibold text-[#4B6B88]">{student.progress}%</span>
                </div>
                <Progress value={student.progress} className="h-2" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">⚠️ Pendiente: {student.pending}</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <MessageSquare className="w-4 h-4 mr-1" />
                    Mensaje
                  </Button>
                  <Button size="sm" className="bg-[#4B6B88] hover:bg-[#1E3A5F]">Ver Proyecto</Button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

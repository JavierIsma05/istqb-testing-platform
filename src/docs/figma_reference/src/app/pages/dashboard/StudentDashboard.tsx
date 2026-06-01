import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Progress } from "../../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import {
  FolderKanban,
  FileCheck,
  Bug,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Target,
  BarChart3,
  Calendar,
  ArrowRight,
  AlertTriangle
} from "lucide-react";
import { Link } from "react-router";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function StudentDashboard() {
  // Mock Data
  const stats = [
    {
      title: "Proyectos Activos",
      value: "2",
      icon: FolderKanban,
      change: "+1 este mes",
      color: "text-[#4B6B88]",
      bgColor: "bg-[#E0F2FE]"
    },
    {
      title: "Casos de Prueba",
      value: "48",
      icon: FileCheck,
      change: "12 pendientes",
      color: "text-[#22C55E]",
      bgColor: "bg-green-100"
    },
    {
      title: "Cobertura",
      value: "87%",
      icon: Target,
      change: "+5% esta semana",
      color: "text-[#7DD3FC]",
      bgColor: "bg-blue-100"
    },
    {
      title: "Defectos Abiertos",
      value: "5",
      icon: Bug,
      change: "2 críticos",
      color: "text-[#EF4444]",
      bgColor: "bg-red-100"
    }
  ];

  const projects = [
    {
      id: 1,
      name: "Sistema de Gestión Académica",
      status: "En Ejecución",
      progress: 65,
      dueDate: "15 Jun 2026",
      testCases: 24,
      passed: 18,
      failed: 3,
      pending: 3
    },
    {
      id: 2,
      name: "App Móvil de Biblioteca",
      status: "En Diseño",
      progress: 40,
      dueDate: "30 Jun 2026",
      testCases: 18,
      passed: 8,
      failed: 2,
      pending: 8
    }
  ];

  const recentActivity = [
    { action: "Caso de prueba ejecutado", item: "TC-045", time: "Hace 2 horas", status: "passed" },
    { action: "Defecto registrado", item: "DEF-023", time: "Hace 4 horas", status: "defect" },
    { action: "Plan de pruebas actualizado", item: "Plan v2.1", time: "Hace 1 día", status: "updated" },
    { action: "Requisito agregado", item: "REQ-089", time: "Hace 2 días", status: "new" },
  ];

  const coverageData = [
    { name: "Requisitos", cubiertos: 28, noCubiertos: 4 },
    { name: "Funcionales", cubiertos: 35, noCubiertos: 5 },
    { name: "No Func.", cubiertos: 18, noCubiertos: 8 },
  ];

  const executionTrend = [
    { week: "Sem 1", passed: 8, failed: 2, blocked: 1 },
    { week: "Sem 2", passed: 15, failed: 3, blocked: 2 },
    { week: "Sem 3", passed: 22, failed: 4, blocked: 1 },
    { week: "Sem 4", passed: 26, failed: 5, blocked: 2 },
  ];

  const defectsByPriority = [
    { name: "Crítico", value: 2, color: "#EF4444" },
    { name: "Alto", value: 5, color: "#FACC15" },
    { name: "Medio", value: 8, color: "#7DD3FC" },
    { name: "Bajo", value: 3, color: "#22C55E" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F] mb-2">Dashboard Estudiante</h1>
        <p className="text-muted-foreground">Bienvenido de vuelta, Juan Pérez</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="border-l-4" style={{ borderLeftColor: stat.color.replace('text-', '') }}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <div className={`${stat.bgColor} p-2 rounded-lg`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-[#1E3A5F]">{stat.value}</div>
                <p className="text-xs text-muted-foreground mt-1">{stat.change}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Projects Overview */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Mis Proyectos</CardTitle>
                <CardDescription>Proyectos de titulación activos</CardDescription>
              </div>
              <Link to="/dashboard/projects">
                <Button variant="outline" size="sm">
                  Ver todos
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {projects.map((project) => (
              <div key={project.id} className="p-4 border border-border rounded-lg space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-[#1E3A5F]">{project.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className="bg-[#E0F2FE] text-[#4B6B88]">{project.status}</Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {project.dueDate}
                      </span>
                    </div>
                  </div>
                  <Link to={`/dashboard/projects/${project.id}`}>
                    <Button variant="ghost" size="sm">Ver</Button>
                  </Link>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progreso</span>
                    <span className="font-semibold text-[#4B6B88]">{project.progress}%</span>
                  </div>
                  <Progress value={project.progress} className="h-2" />
                </div>

                <div className="grid grid-cols-4 gap-2 text-center">
                  <div>
                    <p className="text-xs text-muted-foreground">Total</p>
                    <p className="text-sm font-semibold">{project.testCases}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Passed</p>
                    <p className="text-sm font-semibold text-[#22C55E]">{project.passed}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Failed</p>
                    <p className="text-sm font-semibold text-[#EF4444]">{project.failed}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Pending</p>
                    <p className="text-sm font-semibold text-[#FACC15]">{project.pending}</p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Activity Feed */}
        <Card>
          <CardHeader>
            <CardTitle>Actividad Reciente</CardTitle>
            <CardDescription>Últimas actualizaciones en tus proyectos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-3 pb-3 border-b last:border-0">
                  <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    activity.status === 'passed' ? 'bg-[#22C55E]' :
                    activity.status === 'defect' ? 'bg-[#EF4444]' :
                    activity.status === 'updated' ? 'bg-[#7DD3FC]' : 'bg-[#FACC15]'
                  }`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[#1E3A5F]">{activity.action}</p>
                    <p className="text-sm font-medium text-muted-foreground">{activity.item}</p>
                    <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                  </div>
                  {activity.status === 'passed' && <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />}
                  {activity.status === 'defect' && <AlertCircle className="w-4 h-4 text-[#EF4444]" />}
                  {activity.status === 'updated' && <Clock className="w-4 h-4 text-[#7DD3FC]" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <Tabs defaultValue="coverage" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="coverage">Cobertura</TabsTrigger>
          <TabsTrigger value="execution">Ejecución</TabsTrigger>
          <TabsTrigger value="defects">Defectos</TabsTrigger>
        </TabsList>

        <TabsContent value="coverage">
          <Card>
            <CardHeader>
              <CardTitle>Cobertura de Pruebas</CardTitle>
              <CardDescription>Distribución de cobertura por tipo</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={coverageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="cubiertos" fill="#4B6B88" name="Cubiertos" />
                  <Bar dataKey="noCubiertos" fill="#E0F2FE" name="No Cubiertos" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="execution">
          <Card>
            <CardHeader>
              <CardTitle>Tendencia de Ejecución</CardTitle>
              <CardDescription>Resultados de ejecución por semana</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={executionTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="passed" stroke="#22C55E" name="Pasados" strokeWidth={2} />
                  <Line type="monotone" dataKey="failed" stroke="#EF4444" name="Fallidos" strokeWidth={2} />
                  <Line type="monotone" dataKey="blocked" stroke="#FACC15" name="Bloqueados" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="defects">
          <Card>
            <CardHeader>
              <CardTitle>Defectos por Prioridad</CardTitle>
              <CardDescription>Distribución de defectos activos</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={defectsByPriority}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {defectsByPriority.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Acciones Rápidas</CardTitle>
          <CardDescription>Tareas frecuentes</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <Link to="/dashboard/test-cases">
              <Button variant="outline" className="w-full justify-start">
                <FileCheck className="w-4 h-4 mr-2" />
                Crear Caso de Prueba
              </Button>
            </Link>
            <Link to="/dashboard/test-execution">
              <Button variant="outline" className="w-full justify-start">
                <TrendingUp className="w-4 h-4 mr-2" />
                Ejecutar Pruebas
              </Button>
            </Link>
            <Link to="/dashboard/defects">
              <Button variant="outline" className="w-full justify-start">
                <AlertTriangle className="w-4 h-4 mr-2" />
                Registrar Defecto
              </Button>
            </Link>
            <Link to="/dashboard/reports">
              <Button variant="outline" className="w-full justify-start">
                <BarChart3 className="w-4 h-4 mr-2" />
                Generar Reporte
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

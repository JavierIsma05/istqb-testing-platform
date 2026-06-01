import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Users, FolderKanban, GraduationCap, Activity, TrendingUp, ArrowUp } from "lucide-react";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function AdminDashboard() {
  const stats = [
    { title: "Total Usuarios", value: "156", change: "+12%", icon: Users, color: "text-[#4B6B88]" },
    { title: "Proyectos Totales", value: "48", change: "+8%", icon: FolderKanban, color: "text-[#22C55E]" },
    { title: "Tutores Activos", value: "24", change: "+5%", icon: GraduationCap, color: "text-[#7DD3FC]" },
    { title: "Estudiantes", value: "108", change: "+15%", icon: Users, color: "text-[#FACC15]" },
  ];

  const projectData = [
    { month: "Ene", activos: 12, finalizados: 3 },
    { month: "Feb", activos: 15, finalizados: 5 },
    { month: "Mar", activos: 18, finalizados: 4 },
    { month: "Abr", activos: 22, finalizados: 8 },
    { month: "May", activos: 28, finalizados: 6 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F] mb-2">Dashboard Administrador</h1>
        <p className="text-muted-foreground">Panel de control y estadísticas globales</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-[#1E3A5F]">{stat.value}</div>
                <p className="text-xs text-[#22C55E] flex items-center gap-1 mt-1">
                  <ArrowUp className="w-3 h-3" />
                  {stat.change} vs mes anterior
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tendencia de Proyectos</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={projectData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="activos" fill="#4B6B88" name="Activos" />
              <Bar dataKey="finalizados" fill="#22C55E" name="Finalizados" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

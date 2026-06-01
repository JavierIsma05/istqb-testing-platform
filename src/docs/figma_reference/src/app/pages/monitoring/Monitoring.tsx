import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from "recharts";
import { TrendingUp, Target, Bug, Activity } from "lucide-react";

export default function Monitoring() {
  const coverageData = [
    { name: "Semana 1", cobertura: 30 },
    { name: "Semana 2", cobertura: 45 },
    { name: "Semana 3", cobertura: 68 },
    { name: "Semana 4", cobertura: 87 },
  ];

  const executionData = [
    { name: "Lun", passed: 5, failed: 2, blocked: 1 },
    { name: "Mar", passed: 8, failed: 1, blocked: 0 },
    { name: "Mié", passed: 6, failed: 3, blocked: 2 },
    { name: "Jue", passed: 10, failed: 2, blocked: 1 },
    { name: "Vie", passed: 7, failed: 1, blocked: 0 },
  ];

  const defectTrend = [
    { week: "Sem 1", abiertos: 2, cerrados: 0 },
    { week: "Sem 2", abiertos: 5, cerrados: 1 },
    { week: "Sem 3", abiertos: 8, cerrados: 4 },
    { week: "Sem 4", abiertos: 5, cerrados: 7 },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Monitorización</h1>
        <p className="text-muted-foreground">KPIs y métricas en tiempo real</p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cobertura</p>
                <p className="text-2xl font-bold text-[#4B6B88]">87%</p>
              </div>
              <Target className="w-8 h-8 text-[#4B6B88]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Test Velocity</p>
                <p className="text-2xl font-bold text-[#22C55E]">6.2</p>
              </div>
              <TrendingUp className="w-8 h-8 text-[#22C55E]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Densidad Defectos</p>
                <p className="text-2xl font-bold text-[#EF4444]">0.15</p>
              </div>
              <Bug className="w-8 h-8 text-[#EF4444]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Efectividad</p>
                <p className="text-2xl font-bold text-[#7DD3FC]">92%</p>
              </div>
              <Activity className="w-8 h-8 text-[#7DD3FC]" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="coverage" className="space-y-4">
        <TabsList>
          <TabsTrigger value="coverage">Cobertura</TabsTrigger>
          <TabsTrigger value="execution">Ejecución</TabsTrigger>
          <TabsTrigger value="defects">Defectos</TabsTrigger>
        </TabsList>

        <TabsContent value="coverage">
          <Card>
            <CardHeader>
              <CardTitle>Tendencia de Cobertura</CardTitle>
              <CardDescription>Evolución de cobertura de pruebas por semana</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={coverageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="cobertura" stroke="#4B6B88" fill="#7DD3FC" name="Cobertura %" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="execution">
          <Card>
            <CardHeader>
              <CardTitle>Resultados de Ejecución Diaria</CardTitle>
              <CardDescription>Casos ejecutados por día</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={executionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="passed" fill="#22C55E" name="Pasados" />
                  <Bar dataKey="failed" fill="#EF4444" name="Fallidos" />
                  <Bar dataKey="blocked" fill="#FACC15" name="Bloqueados" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="defects">
          <Card>
            <CardHeader>
              <CardTitle>Tendencia de Defectos</CardTitle>
              <CardDescription>Defectos abiertos vs cerrados por semana</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={defectTrend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="abiertos" stroke="#EF4444" strokeWidth={2} name="Abiertos" />
                  <Line type="monotone" dataKey="cerrados" stroke="#22C55E" strokeWidth={2} name="Cerrados" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

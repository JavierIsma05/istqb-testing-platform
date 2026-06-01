import { useParams } from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Progress } from "../../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Calendar, Users, Target, FileText, TestTube, Bug, ArrowLeft } from "lucide-react";
import { Link } from "react-router";

export default function ProjectDetail() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/dashboard/projects">
          <Button variant="outline" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Sistema de Gestión Académica</h1>
          <p className="text-muted-foreground">Proyecto de titulación - ID: PRJ-{id}</p>
        </div>
        <Badge className="bg-[#22C55E] text-white">Activo</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cobertura</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#4B6B88]">87%</div>
            <Progress value={87} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Casos de Prueba</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#1E3A5F]">24</div>
            <p className="text-xs text-muted-foreground mt-1">18 pasados, 3 fallidos</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Defectos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#EF4444]">5</div>
            <p className="text-xs text-muted-foreground mt-1">2 críticos</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Requisitos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[#1E3A5F]">32</div>
            <p className="text-xs text-muted-foreground mt-1">28 cubiertos</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Resumen</TabsTrigger>
          <TabsTrigger value="requirements">Requisitos</TabsTrigger>
          <TabsTrigger value="testcases">Casos de Prueba</TabsTrigger>
          <TabsTrigger value="defects">Defectos</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Información del Proyecto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Tutor</p>
                    <p className="font-medium">Dr. María González</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Fecha Límite</p>
                    <p className="font-medium">15 Jun 2026</p>
                  </div>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Descripción</p>
                <p className="text-sm">
                  Plataforma web completa para la gestión integral de estudiantes, cursos, calificaciones 
                  y asistencia en instituciones educativas.
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">Progreso General</p>
                <Progress value={65} className="h-3" />
                <p className="text-sm text-right mt-1 font-semibold text-[#4B6B88]">65%</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="requirements">
          <Card>
            <CardHeader>
              <CardTitle>Requisitos del Proyecto</CardTitle>
              <CardDescription>Lista de requisitos funcionales y no funcionales</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">32 requisitos totales - Ver módulo de Requisitos para más detalles</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="testcases">
          <Card>
            <CardHeader>
              <CardTitle>Casos de Prueba</CardTitle>
              <CardDescription>Casos de prueba diseñados para este proyecto</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">24 casos de prueba - Ver módulo de Casos de Prueba para más detalles</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="defects">
          <Card>
            <CardHeader>
              <CardTitle>Defectos Registrados</CardTitle>
              <CardDescription>Defectos encontrados durante las pruebas</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">5 defectos activos - Ver módulo de Defectos para más detalles</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

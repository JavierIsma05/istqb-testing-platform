import { useState } from "react";
import { Link } from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { Plus, Search, Filter, MoreVertical, Calendar, Users, Target, Eye, Edit, Trash2, FolderKanban } from "lucide-react";

export default function ProjectsList() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchTerm, setSearchTerm] = useState("");

  const projects = [
    {
      id: 1,
      name: "Sistema de Gestión Académica",
      description: "Plataforma web para gestión de estudiantes, cursos y calificaciones",
      status: "Activo",
      progress: 65,
      tutor: "Dr. María González",
      startDate: "01 Mar 2026",
      dueDate: "15 Jun 2026",
      testCases: 24,
      requirements: 32,
      defects: 5,
      coverage: 87
    },
    {
      id: 2,
      name: "App Móvil de Biblioteca",
      description: "Aplicación móvil para reserva y gestión de libros",
      status: "En Revisión",
      progress: 40,
      tutor: "Ing. Carlos Ramírez",
      startDate: "15 Mar 2026",
      dueDate: "30 Jun 2026",
      testCases: 18,
      requirements: 24,
      defects: 3,
      coverage: 68
    },
    {
      id: 3,
      name: "Sistema de Control de Inventario",
      description: "Sistema para gestión de inventario y logística",
      status: "Finalizado",
      progress: 100,
      tutor: "Dra. Ana Silva",
      startDate: "01 Feb 2026",
      dueDate: "30 Abr 2026",
      testCases: 42,
      requirements: 48,
      defects: 0,
      coverage: 95
    },
    {
      id: 4,
      name: "Portal de Servicios Universitarios",
      description: "Portal web para trámites y servicios estudiantiles",
      status: "Activo",
      progress: 28,
      tutor: "Dr. Roberto Méndez",
      startDate: "01 Abr 2026",
      dueDate: "30 Jul 2026",
      testCases: 12,
      requirements: 28,
      defects: 2,
      coverage: 45
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Activo":
        return "bg-[#22C55E] text-white";
      case "En Revisión":
        return "bg-[#FACC15] text-[#1E3A5F]";
      case "Finalizado":
        return "bg-[#4B6B88] text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const filteredProjects = projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Proyectos</h1>
          <p className="text-muted-foreground">Gestiona tus proyectos de titulación</p>
        </div>
        <Link to="/dashboard/projects/create">
          <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
            <Plus className="w-4 h-4 mr-2" />
            Nuevo Proyecto
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar proyectos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select defaultValue="all">
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Estado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los estados</SelectItem>
                <SelectItem value="active">Activo</SelectItem>
                <SelectItem value="review">En Revisión</SelectItem>
                <SelectItem value="finished">Finalizado</SelectItem>
              </SelectContent>
            </Select>
            <Select defaultValue="all">
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Tutor" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos los tutores</SelectItem>
                <SelectItem value="tutor1">Dr. María González</SelectItem>
                <SelectItem value="tutor2">Ing. Carlos Ramírez</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* View Toggle */}
      <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "grid" | "list")}>
        <TabsList>
          <TabsTrigger value="grid">Vista de Tarjetas</TabsTrigger>
          <TabsTrigger value="list">Vista de Lista</TabsTrigger>
        </TabsList>

        {/* Grid View */}
        <TabsContent value="grid" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {filteredProjects.map((project) => (
              <Card key={project.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <FolderKanban className="w-5 h-5 text-[#4B6B88]" />
                        <CardTitle className="text-lg">{project.name}</CardTitle>
                      </div>
                      <CardDescription>{project.description}</CardDescription>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="w-4 h-4 mr-2" />
                          Ver Detalles
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Edit className="w-4 h-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-[#EF4444]">
                          <Trash2 className="w-4 h-4 mr-2" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge className={getStatusColor(project.status)}>
                      {project.status}
                    </Badge>
                    <span className="text-sm text-muted-foreground flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {project.dueDate}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Progreso del Proyecto</span>
                      <span className="font-semibold text-[#4B6B88]">{project.progress}%</span>
                    </div>
                    <Progress value={project.progress} className="h-2" />
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded bg-[#E0F2FE] flex items-center justify-center">
                        <Target className="w-4 h-4 text-[#4B6B88]" />
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Cobertura</p>
                        <p className="font-semibold">{project.coverage}%</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded bg-green-100 flex items-center justify-center">
                        <span className="text-xs font-bold text-green-600">{project.testCases}</span>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Casos</p>
                        <p className="font-semibold">{project.testCases}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-3 border-t">
                    <Users className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Tutor:</span>
                    <span className="text-sm font-medium">{project.tutor}</span>
                  </div>

                  <Link to={`/dashboard/projects/${project.id}`}>
                    <Button variant="outline" className="w-full">
                      <Eye className="w-4 h-4 mr-2" />
                      Ver Proyecto
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* List View */}
        <TabsContent value="list">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b bg-[#F5F7FA]">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Proyecto</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Estado</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Tutor</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Progreso</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Cobertura</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Fecha Límite</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-muted-foreground">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredProjects.map((project) => (
                      <tr key={project.id} className="border-b hover:bg-[#F5F7FA] transition-colors">
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-[#E0F2FE] flex items-center justify-center">
                              <FolderKanban className="w-5 h-5 text-[#4B6B88]" />
                            </div>
                            <div>
                              <p className="font-medium text-[#1E3A5F]">{project.name}</p>
                              <p className="text-sm text-muted-foreground">{project.testCases} casos de prueba</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <Badge className={getStatusColor(project.status)}>
                            {project.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-4 text-sm">{project.tutor}</td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-2">
                            <Progress value={project.progress} className="h-2 w-20" />
                            <span className="text-sm font-medium">{project.progress}%</span>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <span className="text-sm font-medium text-[#4B6B88]">{project.coverage}%</span>
                        </td>
                        <td className="px-4 py-4 text-sm">{project.dueDate}</td>
                        <td className="px-4 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Link to={`/dashboard/projects/${project.id}`}>
                              <Button variant="ghost" size="sm">
                                <Eye className="w-4 h-4" />
                              </Button>
                            </Link>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm">
                                  <MoreVertical className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>Editar</DropdownMenuItem>
                                <DropdownMenuItem>Duplicar</DropdownMenuItem>
                                <DropdownMenuItem className="text-[#EF4444]">Eliminar</DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

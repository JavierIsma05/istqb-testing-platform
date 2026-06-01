import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Plus, Search, Filter, TestTube, CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { toast } from "sonner";

export default function TestCasesList() {
  const [searchTerm, setSearchTerm] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const testCases = [
    {
      id: "TC-001",
      title: "Validar inicio de sesión con credenciales correctas",
      description: "Verificar que el usuario pueda iniciar sesión con email y contraseña válidos",
      priority: "Alta",
      status: "Passed",
      technique: "Partición de Equivalencia",
      requirement: "REQ-001",
      lastExecution: "23 May 2026",
      executedBy: "Juan Pérez"
    },
    {
      id: "TC-002",
      title: "Validar registro de nuevo estudiante",
      description: "Comprobar el flujo completo de registro de un estudiante nuevo",
      priority: "Alta",
      status: "Failed",
      technique: "Caja Negra",
      requirement: "REQ-002",
      lastExecution: "22 May 2026",
      executedBy: "María García"
    },
    {
      id: "TC-003",
      title: "Búsqueda de libros por título",
      description: "Verificar funcionalidad de búsqueda en el catálogo",
      priority: "Media",
      status: "Pending",
      technique: "Valores Límite",
      requirement: "REQ-015",
      lastExecution: "-",
      executedBy: "-"
    },
    {
      id: "TC-004",
      title: "Reserva de libro disponible",
      description: "Validar proceso de reserva cuando hay ejemplares disponibles",
      priority: "Alta",
      status: "Passed",
      technique: "Tabla de Decisión",
      requirement: "REQ-018",
      lastExecution: "23 May 2026",
      executedBy: "Juan Pérez"
    },
    {
      id: "TC-005",
      title: "Validar carga de archivos PDF",
      description: "Comprobar que se puedan cargar documentos PDF correctamente",
      priority: "Media",
      status: "Blocked",
      technique: "Caja Negra",
      requirement: "REQ-025",
      lastExecution: "20 May 2026",
      executedBy: "Ana Silva"
    },
    {
      id: "TC-006",
      title: "Generación de reporte de estadísticas",
      description: "Verificar que el reporte se genere con datos correctos",
      priority: "Baja",
      status: "Passed",
      technique: "Caja Blanca",
      requirement: "REQ-030",
      lastExecution: "21 May 2026",
      executedBy: "Carlos Ruiz"
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Passed":
        return "bg-[#22C55E] text-white";
      case "Failed":
        return "bg-[#EF4444] text-white";
      case "Pending":
        return "bg-[#FACC15] text-[#1E3A5F]";
      case "Blocked":
        return "bg-gray-500 text-white";
      default:
        return "bg-gray-300 text-gray-700";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Passed":
        return <CheckCircle2 className="w-4 h-4" />;
      case "Failed":
        return <XCircle className="w-4 h-4" />;
      case "Pending":
        return <Clock className="w-4 h-4" />;
      case "Blocked":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "Alta":
        return "border-l-[#EF4444]";
      case "Media":
        return "border-l-[#FACC15]";
      case "Baja":
        return "border-l-[#22C55E]";
      default:
        return "border-l-gray-400";
    }
  };

  const handleCreateTestCase = () => {
    toast.success("Caso de prueba creado exitosamente");
    setDialogOpen(false);
  };

  const filteredTestCases = testCases.filter(tc =>
    tc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tc.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Casos de Prueba</h1>
          <p className="text-muted-foreground">Diseña y gestiona casos de prueba según ISTQB</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Caso de Prueba
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crear Caso de Prueba</DialogTitle>
              <DialogDescription>
                Completa la información del nuevo caso de prueba
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>ID del Caso</Label>
                  <Input placeholder="TC-XXX" />
                </div>
                <div className="space-y-2">
                  <Label>Requisito</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="req1">REQ-001</SelectItem>
                      <SelectItem value="req2">REQ-002</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Título</Label>
                <Input placeholder="Título descriptivo del caso de prueba" />
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Textarea placeholder="Descripción detallada del caso de prueba" rows={3} />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Prioridad</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high">Alta</SelectItem>
                      <SelectItem value="medium">Media</SelectItem>
                      <SelectItem value="low">Baja</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Técnica ISTQB</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="blackbox">Caja Negra</SelectItem>
                      <SelectItem value="whitebox">Caja Blanca</SelectItem>
                      <SelectItem value="equivalence">Partición Equivalencia</SelectItem>
                      <SelectItem value="boundary">Valores Límite</SelectItem>
                      <SelectItem value="decision">Tabla Decisión</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Nivel de Prueba</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unit">Unitaria</SelectItem>
                      <SelectItem value="integration">Integración</SelectItem>
                      <SelectItem value="system">Sistema</SelectItem>
                      <SelectItem value="acceptance">Aceptación</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Precondiciones</Label>
                <Textarea placeholder="Condiciones previas para ejecutar el caso" rows={2} />
              </div>
              <div className="space-y-2">
                <Label>Pasos de Ejecución</Label>
                <Textarea placeholder="1. Paso 1&#10;2. Paso 2&#10;3. Paso 3" rows={3} />
              </div>
              <div className="space-y-2">
                <Label>Resultado Esperado</Label>
                <Textarea placeholder="Descripción del resultado esperado" rows={2} />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleCreateTestCase}>
                Crear Caso de Prueba
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Casos</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">{testCases.length}</p>
              </div>
              <TestTube className="w-8 h-8 text-[#4B6B88]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pasados</p>
                <p className="text-2xl font-bold text-[#22C55E]">
                  {testCases.filter(tc => tc.status === "Passed").length}
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-[#22C55E]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Fallidos</p>
                <p className="text-2xl font-bold text-[#EF4444]">
                  {testCases.filter(tc => tc.status === "Failed").length}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-[#EF4444]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pendientes</p>
                <p className="text-2xl font-bold text-[#FACC15]">
                  {testCases.filter(tc => tc.status === "Pending").length}
                </p>
              </div>
              <Clock className="w-8 h-8 text-[#FACC15]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar casos de prueba..."
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
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="passed">Passed</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
              </SelectContent>
            </Select>
            <Select defaultValue="all">
              <SelectTrigger className="w-full md:w-[180px]">
                <SelectValue placeholder="Prioridad" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="high">Alta</SelectItem>
                <SelectItem value="medium">Media</SelectItem>
                <SelectItem value="low">Baja</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Filter className="w-4 h-4 mr-2" />
              Más Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Cases List */}
      <div className="space-y-3">
        {filteredTestCases.map((testCase) => (
          <Card key={testCase.id} className={`border-l-4 ${getPriorityColor(testCase.priority)} hover:shadow-md transition-shadow`}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <TestTube className="w-5 h-5 text-[#4B6B88]" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="font-mono text-xs">
                          {testCase.id}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {testCase.requirement}
                        </Badge>
                      </div>
                      <h3 className="font-semibold text-[#1E3A5F] mb-1">{testCase.title}</h3>
                      <p className="text-sm text-muted-foreground">{testCase.description}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    <div className="flex items-center gap-1">
                      <span className="text-muted-foreground">Técnica:</span>
                      <Badge variant="secondary" className="bg-[#E0F2FE] text-[#4B6B88]">
                        {testCase.technique}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-muted-foreground">Prioridad:</span>
                      <span className="font-medium">{testCase.priority}</span>
                    </div>
                    {testCase.lastExecution !== "-" && (
                      <>
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Última ejecución:</span>
                          <span className="font-medium">{testCase.lastExecution}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Por:</span>
                          <span className="font-medium">{testCase.executedBy}</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-3">
                  <Badge className={`${getStatusColor(testCase.status)} flex items-center gap-1`}>
                    {getStatusIcon(testCase.status)}
                    {testCase.status}
                  </Badge>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      Ver Detalle
                    </Button>
                    <Button size="sm" className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
                      Ejecutar
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

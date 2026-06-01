import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Plus, FileText } from "lucide-react";

export default function RequirementsList() {
  const requirements = [
    { id: "REQ-001", title: "Login de usuarios", type: "Funcional", priority: "Alta", coverage: "100%", status: "Aprobado" },
    { id: "REQ-002", title: "Registro de estudiantes", type: "Funcional", priority: "Alta", coverage: "85%", status: "Aprobado" },
    { id: "REQ-015", title: "Búsqueda de libros", type: "Funcional", priority: "Media", coverage: "60%", status: "En revisión" },
    { id: "REQ-025", title: "Carga de archivos PDF", type: "Funcional", priority: "Media", coverage: "45%", status: "Pendiente" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Requisitos</h1>
          <p className="text-muted-foreground">Gestión de requisitos funcionales y no funcionales</p>
        </div>
        <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Requisito
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#1E3A5F]">32</div>
            <p className="text-sm text-muted-foreground">Total Requisitos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#22C55E]">28</div>
            <p className="text-sm text-muted-foreground">Cubiertos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#4B6B88]">87%</div>
            <p className="text-sm text-muted-foreground">Cobertura</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#FACC15]">4</div>
            <p className="text-sm text-muted-foreground">Pendientes</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Requisitos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {requirements.map((req) => (
              <div key={req.id} className="p-4 border rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-[#4B6B88]" />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline">{req.id}</Badge>
                      <span className="font-semibold text-[#1E3A5F]">{req.title}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span>Tipo: {req.type}</span>
                      <span>Prioridad: {req.priority}</span>
                      <span>Cobertura: {req.coverage}</span>
                    </div>
                  </div>
                </div>
                <Badge className="bg-[#E0F2FE] text-[#4B6B88]">{req.status}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Plus, Bug, AlertCircle } from "lucide-react";

export default function DefectsList() {
  const defects = [
    { id: "DEF-001", title: "Error al cargar imágenes grandes", severity: "Alto", priority: "Alta", status: "Open", assignedTo: "Dev Team" },
    { id: "DEF-002", title: "Validación incorrecta en formulario", severity: "Medio", priority: "Media", status: "In Fix", assignedTo: "Juan Dev" },
    { id: "DEF-023", title: "Botón no responde en móvil", severity: "Bajo", priority: "Baja", status: "Closed", assignedTo: "María Dev" },
  ];

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      "Open": "bg-[#EF4444] text-white",
      "In Fix": "bg-[#FACC15] text-[#1E3A5F]",
      "Closed": "bg-[#22C55E] text-white"
    };
    return colors[status] || "bg-gray-500 text-white";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Gestión de Defectos</h1>
          <p className="text-muted-foreground">Registro y seguimiento de defectos encontrados</p>
        </div>
        <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
          <Plus className="w-4 h-4 mr-2" />
          Reportar Defecto
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#EF4444]">5</div>
            <p className="text-sm text-muted-foreground">Abiertos</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#FACC15]">3</div>
            <p className="text-sm text-muted-foreground">En Corrección</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#22C55E]">12</div>
            <p className="text-sm text-muted-foreground">Cerrados</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-[#1E3A5F]">20</div>
            <p className="text-sm text-muted-foreground">Total</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Defectos Registrados</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {defects.map((defect) => (
            <div key={defect.id} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <Bug className="w-5 h-5 text-[#EF4444]" />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline">{defect.id}</Badge>
                      <span className="font-semibold text-[#1E3A5F]">{defect.title}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span>Severidad: {defect.severity}</span>
                      <span>Prioridad: {defect.priority}</span>
                      <span>Asignado: {defect.assignedTo}</span>
                    </div>
                  </div>
                </div>
                <Badge className={getStatusColor(defect.status)}>{defect.status}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

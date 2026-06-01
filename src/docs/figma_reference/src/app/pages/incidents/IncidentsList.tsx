import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Plus, AlertTriangle } from "lucide-react";

export default function IncidentsList() {
  const incidents = [
    { id: "INC-001", title: "Riesgo de integración con API externa", probability: "Alta", impact: "Alto", status: "Mitigada" },
    { id: "INC-002", title: "Posible retraso en entrega de módulo", probability: "Media", impact: "Medio", status: "Abierta" },
  ];

  const getRiskColor = (probability: string, impact: string) => {
    if (probability === "Alta" && impact === "Alto") return "bg-[#EF4444]";
    if (probability === "Media" || impact === "Medio") return "bg-[#FACC15]";
    return "bg-[#22C55E]";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Gestión de Incidencias</h1>
          <p className="text-muted-foreground">Registro y seguimiento de riesgos e incidencias</p>
        </div>
        <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
          <Plus className="w-4 h-4 mr-2" />
          Nueva Incidencia
        </Button>
      </div>

      {/* Heatmap visual */}
      <Card>
        <CardHeader>
          <CardTitle>Matriz de Probabilidad-Impacto</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-2 max-w-md">
            <div className="h-16 bg-[#FACC15] rounded flex items-center justify-center text-sm font-semibold">Alto-Bajo</div>
            <div className="h-16 bg-[#EF4444] rounded flex items-center justify-center text-sm font-semibold text-white">Alto-Medio</div>
            <div className="h-16 bg-[#EF4444] rounded flex items-center justify-center text-sm font-semibold text-white">Alto-Alto</div>
            <div className="h-16 bg-[#22C55E] rounded flex items-center justify-center text-sm font-semibold">Medio-Bajo</div>
            <div className="h-16 bg-[#FACC15] rounded flex items-center justify-center text-sm font-semibold">Medio-Medio</div>
            <div className="h-16 bg-[#EF4444] rounded flex items-center justify-center text-sm font-semibold text-white">Medio-Alto</div>
            <div className="h-16 bg-[#22C55E] rounded flex items-center justify-center text-sm font-semibold">Bajo-Bajo</div>
            <div className="h-16 bg-[#22C55E] rounded flex items-center justify-center text-sm font-semibold">Bajo-Medio</div>
            <div className="h-16 bg-[#FACC15] rounded flex items-center justify-center text-sm font-semibold">Bajo-Alto</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Incidencias Registradas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {incidents.map((inc) => (
            <div key={inc.id} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <AlertTriangle className={`w-5 h-5 text-[#EF4444]`} />
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline">{inc.id}</Badge>
                      <span className="font-semibold text-[#1E3A5F]">{inc.title}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground">
                      <span>Probabilidad: {inc.probability}</span>
                      <span>Impacto: {inc.impact}</span>
                    </div>
                  </div>
                </div>
                <Badge className={`${getRiskColor(inc.probability, inc.impact)} text-white`}>
                  {inc.status}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

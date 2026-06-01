import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { CheckCircle2, Circle, Clock } from "lucide-react";

export default function PhasesManagement() {
  const phases = [
    { number: 1, name: "Planificación", description: "Define estrategia y recursos", status: "completed", progress: 100 },
    { number: 2, name: "Análisis", description: "Analiza requisitos y riesgos", status: "completed", progress: 100 },
    { number: 3, name: "Diseño", description: "Diseña casos de prueba", status: "completed", progress: 100 },
    { number: 4, name: "Implementación", description: "Prepara entorno de pruebas", status: "active", progress: 75 },
    { number: 5, name: "Ejecución", description: "Ejecuta casos y registra resultados", status: "pending", progress: 45 },
    { number: 6, name: "Cierre", description: "Genera informes y lecciones aprendidas", status: "pending", progress: 0 },
  ];

  const getPhaseIcon = (status: string) => {
    if (status === "completed") return <CheckCircle2 className="w-6 h-6 text-[#22C55E]" />;
    if (status === "active") return <Clock className="w-6 h-6 text-[#FACC15]" />;
    return <Circle className="w-6 h-6 text-gray-400" />;
  };

  const getPhaseColor = (status: string) => {
    if (status === "completed") return "border-l-[#22C55E]";
    if (status === "active") return "border-l-[#4B6B88]";
    return "border-l-gray-300";
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Fases ISTQB</h1>
        <p className="text-muted-foreground">Gestión del ciclo de vida de pruebas</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Progreso General del Ciclo ISTQB</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Progreso Total</span>
              <span className="font-semibold text-[#4B6B88]">70%</span>
            </div>
            <Progress value={70} className="h-3" />
          </div>
          <p className="text-sm text-muted-foreground">4 de 6 fases completadas</p>
        </CardContent>
      </Card>

      <div className="space-y-4">
        {phases.map((phase) => (
          <Card key={phase.number} className={`border-l-4 ${getPhaseColor(phase.status)}`}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  {getPhaseIcon(phase.status)}
                </div>
                <div className="flex-1 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="font-mono">Fase {phase.number}</Badge>
                        <h3 className="text-lg font-semibold text-[#1E3A5F]">{phase.name}</h3>
                      </div>
                      <p className="text-sm text-muted-foreground">{phase.description}</p>
                    </div>
                    <Badge className={
                      phase.status === "completed" ? "bg-[#22C55E] text-white" :
                      phase.status === "active" ? "bg-[#4B6B88] text-white" :
                      "bg-gray-300 text-gray-700"
                    }>
                      {phase.status === "completed" ? "Completada" : phase.status === "active" ? "En Proceso" : "Pendiente"}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Progreso de la Fase</span>
                      <span className="font-semibold text-[#4B6B88]">{phase.progress}%</span>
                    </div>
                    <Progress value={phase.progress} className="h-2" />
                  </div>
                  {phase.status === "active" && (
                    <div className="flex gap-2 pt-2">
                      <Badge variant="outline" className="text-xs">3 tareas completadas</Badge>
                      <Badge variant="outline" className="text-xs">1 tarea pendiente</Badge>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

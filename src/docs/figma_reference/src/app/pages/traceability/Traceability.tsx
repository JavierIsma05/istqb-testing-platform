import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { GitBranch, FileText, TestTube, Bug, CheckCircle2 } from "lucide-react";

export default function Traceability() {
  const traceabilityMatrix = [
    { req: "REQ-001", testCases: ["TC-001", "TC-002"], defects: [], coverage: "100%" },
    { req: "REQ-002", testCases: ["TC-003"], defects: ["DEF-001"], coverage: "100%" },
    { req: "REQ-015", testCases: ["TC-004", "TC-005"], defects: [], coverage: "85%" },
    { req: "REQ-025", testCases: ["TC-006"], defects: ["DEF-002", "DEF-003"], coverage: "60%" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Matriz de Trazabilidad</h1>
        <p className="text-muted-foreground">Relación entre requisitos, casos de prueba y defectos</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cobertura Total</p>
                <p className="text-2xl font-bold text-[#4B6B88]">87%</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-[#22C55E]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Requisitos Cubiertos</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">28/32</p>
              </div>
              <FileText className="w-8 h-8 text-[#4B6B88]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Casos de Prueba</p>
                <p className="text-2xl font-bold text-[#1E3A5F]">48</p>
              </div>
              <TestTube className="w-8 h-8 text-[#7DD3FC]" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Matriz de Trazabilidad</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b bg-[#F5F7FA]">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Requisito</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Casos de Prueba</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Defectos</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Cobertura</th>
                </tr>
              </thead>
              <tbody>
                {traceabilityMatrix.map((item, index) => (
                  <tr key={index} className="border-b hover:bg-[#F5F7FA]">
                    <td className="px-4 py-3">
                      <Badge variant="outline">{item.req}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {item.testCases.map((tc) => (
                          <Badge key={tc} className="bg-[#E0F2FE] text-[#4B6B88] text-xs">
                            <TestTube className="w-3 h-3 mr-1" />
                            {tc}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {item.defects.length > 0 ? (
                          item.defects.map((def) => (
                            <Badge key={def} className="bg-red-100 text-[#EF4444] text-xs">
                              <Bug className="w-3 h-3 mr-1" />
                              {def}
                            </Badge>
                          ))
                        ) : (
                          <span className="text-sm text-muted-foreground">Sin defectos</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={`${parseInt(item.coverage) >= 80 ? 'bg-[#22C55E]' : 'bg-[#FACC15]'} text-white`}>
                        {item.coverage}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

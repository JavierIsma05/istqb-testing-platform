import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { FileBarChart, Download, Eye, FileText } from "lucide-react";
import { Badge } from "../../components/ui/badge";
import { toast } from "sonner";

export default function Reports() {
  const reports = [
    { name: "Informe de Cobertura", type: "Cobertura", date: "24 May 2026", status: "Generado" },
    { name: "Reporte de Ejecución", type: "Ejecución", date: "23 May 2026", status: "Generado" },
    { name: "Análisis de Defectos", type: "Defectos", date: "22 May 2026", status: "Generado" },
  ];

  const handleGenerate = () => toast.success("Generando reporte PDF...");
  const handleDownload = () => toast.success("Descargando PDF...");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Informes y Reportes</h1>
          <p className="text-muted-foreground">Genera informes profesionales en PDF</p>
        </div>
        <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleGenerate}>
          <FileBarChart className="w-4 h-4 mr-2" />
          Generar Nuevo Reporte
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={handleGenerate}>
          <CardHeader className="text-center">
            <FileText className="w-12 h-12 mx-auto text-[#4B6B88] mb-2" />
            <CardTitle className="text-lg">Informe de Cobertura</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground">Reporte completo de cobertura de pruebas</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={handleGenerate}>
          <CardHeader className="text-center">
            <FileText className="w-12 h-12 mx-auto text-[#22C55E] mb-2" />
            <CardTitle className="text-lg">Reporte de Ejecución</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground">Resultados de ejecución de casos de prueba</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={handleGenerate}>
          <CardHeader className="text-center">
            <FileText className="w-12 h-12 mx-auto text-[#EF4444] mb-2" />
            <CardTitle className="text-lg">Análisis de Defectos</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-muted-foreground">Estadísticas y métricas de defectos</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reportes Generados</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {reports.map((report, index) => (
            <div key={index} className="p-4 border rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileBarChart className="w-5 h-5 text-[#4B6B88]" />
                <div>
                  <h3 className="font-semibold text-[#1E3A5F]">{report.name}</h3>
                  <p className="text-sm text-muted-foreground">Tipo: {report.type} • {report.date}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge className="bg-[#22C55E] text-white">{report.status}</Badge>
                <Button variant="outline" size="sm">
                  <Eye className="w-4 h-4 mr-1" />
                  Ver
                </Button>
                <Button size="sm" className="bg-[#4B6B88] hover:bg-[#1E3A5F]" onClick={handleDownload}>
                  <Download className="w-4 h-4 mr-1" />
                  Descargar
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

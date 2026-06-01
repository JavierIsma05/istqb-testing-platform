import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Play, CheckCircle2, XCircle, Upload } from "lucide-react";
import { Textarea } from "../../components/ui/textarea";
import { Label } from "../../components/ui/label";
import { toast } from "sonner";

export default function TestExecution() {
  const handleExecute = () => toast.success("Resultado de ejecución registrado");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#1E3A5F]">Ejecución de Pruebas</h1>
        <p className="text-muted-foreground">Ejecuta casos de prueba y registra resultados</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <Badge variant="outline" className="mb-2">TC-001</Badge>
                <CardTitle>Validar inicio de sesión</CardTitle>
              </div>
              <Badge className="bg-[#FACC15] text-[#1E3A5F]">Pendiente</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Precondiciones:</h4>
              <p className="text-sm text-muted-foreground">Usuario registrado en el sistema</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Pasos:</h4>
              <ol className="text-sm text-muted-foreground list-decimal list-inside space-y-1">
                <li>Abrir la aplicación</li>
                <li>Ingresar email válido</li>
                <li>Ingresar contraseña válida</li>
                <li>Hacer clic en "Iniciar Sesión"</li>
              </ol>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Resultado Esperado:</h4>
              <p className="text-sm text-muted-foreground">El usuario debe ser redirigido al dashboard</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Registrar Resultado</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <Button variant="outline" className="flex-col h-auto py-4 border-2 border-[#22C55E] hover:bg-green-50" onClick={handleExecute}>
                <CheckCircle2 className="w-8 h-8 text-[#22C55E] mb-2" />
                <span className="font-semibold">Passed</span>
              </Button>
              <Button variant="outline" className="flex-col h-auto py-4 border-2 border-[#EF4444] hover:bg-red-50" onClick={handleExecute}>
                <XCircle className="w-8 h-8 text-[#EF4444] mb-2" />
                <span className="font-semibold">Failed</span>
              </Button>
              <Button variant="outline" className="flex-col h-auto py-4 border-2 border-[#FACC15]" onClick={handleExecute}>
                <Play className="w-8 h-8 text-[#FACC15] mb-2" />
                <span className="font-semibold">Blocked</span>
              </Button>
            </div>

            <div className="space-y-2">
              <Label>Observaciones</Label>
              <Textarea placeholder="Describe el resultado de la ejecución..." rows={4} />
            </div>

            <div className="space-y-2">
              <Label>Evidencias</Label>
              <Button variant="outline" className="w-full">
                <Upload className="w-4 h-4 mr-2" />
                Adjuntar Screenshots
              </Button>
            </div>

            <Button className="w-full bg-[#4B6B88] hover:bg-[#1E3A5F]">
              Guardar Resultado
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

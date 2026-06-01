import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Plus, ClipboardList, Calendar } from "lucide-react";
import { Link } from "react-router";

export default function TestPlanList() {
  const plans = [
    { id: 1, name: "Plan de Pruebas v2.1", version: "2.1", status: "Aprobado", date: "15 May 2026", author: "Juan Pérez" },
    { id: 2, name: "Plan de Pruebas v1.5", version: "1.5", status: "En Revisión", date: "10 May 2026", author: "María García" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Plan de Pruebas</h1>
          <p className="text-muted-foreground">Gestión de planes de prueba según ISTQB</p>
        </div>
        <Link to="/dashboard/test-plans/create">
          <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
            <Plus className="w-4 h-4 mr-2" />
            Nuevo Plan
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Planes de Prueba</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {plans.map((plan) => (
            <div key={plan.id} className="p-4 border rounded-lg">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <ClipboardList className="w-5 h-5 text-[#4B6B88]" />
                  <div>
                    <h3 className="font-semibold text-[#1E3A5F]">{plan.name}</h3>
                    <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                      <span>Versión: {plan.version}</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {plan.date}
                      </span>
                      <span>Por: {plan.author}</span>
                    </div>
                  </div>
                </div>
                <Badge className="bg-[#22C55E] text-white">{plan.status}</Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

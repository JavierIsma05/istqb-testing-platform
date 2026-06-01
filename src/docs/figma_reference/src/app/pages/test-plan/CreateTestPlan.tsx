import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Badge } from "../../components/ui/badge";
import { ArrowLeft, Save, Check } from "lucide-react";
import { Link } from "react-router";
import { toast } from "sonner";

export default function CreateTestPlan() {
  const [currentStep, setCurrentStep] = useState(1);
  
  const steps = [
    { number: 1, title: "Información General", completed: false },
    { number: 2, title: "Alcance y Objetivos", completed: false },
    { number: 3, title: "Criterios", completed: false },
    { number: 4, title: "Recursos y Calendario", completed: false },
  ];

  const handleNext = () => {
    if (currentStep < 4) setCurrentStep(currentStep + 1);
  };

  const handleSubmit = () => {
    toast.success("Plan de pruebas creado exitosamente");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/dashboard/test-plans">
          <Button variant="outline" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Crear Plan de Pruebas</h1>
          <p className="text-muted-foreground">Asistente paso a paso</p>
        </div>
      </div>

      {/* Stepper */}
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {steps.map((step, index) => (
          <div key={step.number} className="flex items-center flex-1">
            <div className="flex flex-col items-center flex-1">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold
                ${currentStep === step.number ? 'bg-[#4B6B88] text-white' : 
                  currentStep > step.number ? 'bg-[#22C55E] text-white' : 'bg-gray-200 text-gray-600'}`}>
                {currentStep > step.number ? <Check className="w-5 h-5" /> : step.number}
              </div>
              <span className="text-xs mt-2 text-center">{step.title}</span>
            </div>
            {index < steps.length - 1 && (
              <div className={`h-0.5 flex-1 ${currentStep > step.number ? 'bg-[#22C55E]' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Paso {currentStep}: {steps[currentStep - 1].title}</CardTitle>
          <CardDescription>Completa la información requerida</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {currentStep === 1 && (
            <>
              <div className="space-y-2">
                <Label>Nombre del Plan</Label>
                <Input placeholder="Plan de Pruebas v1.0" />
              </div>
              <div className="space-y-2">
                <Label>Descripción</Label>
                <Textarea placeholder="Descripción del plan de pruebas..." rows={4} />
              </div>
            </>
          )}
          {currentStep === 2 && (
            <>
              <div className="space-y-2">
                <Label>Alcance</Label>
                <Textarea placeholder="Define el alcance de las pruebas..." rows={4} />
              </div>
              <div className="space-y-2">
                <Label>Objetivos</Label>
                <Textarea placeholder="Objetivos principales del plan..." rows={4} />
              </div>
            </>
          )}
          {currentStep === 3 && (
            <>
              <div className="space-y-2">
                <Label>Criterios de Entrada</Label>
                <Textarea placeholder="Condiciones para iniciar las pruebas..." rows={3} />
              </div>
              <div className="space-y-2">
                <Label>Criterios de Salida</Label>
                <Textarea placeholder="Condiciones para finalizar las pruebas..." rows={3} />
              </div>
            </>
          )}
          {currentStep === 4 && (
            <>
              <div className="space-y-2">
                <Label>Recursos Necesarios</Label>
                <Textarea placeholder="Hardware, software, personal..." rows={3} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Fecha de Inicio</Label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <Label>Fecha de Finalización</Label>
                  <Input type="date" />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => currentStep > 1 && setCurrentStep(currentStep - 1)} disabled={currentStep === 1}>
          Anterior
        </Button>
        {currentStep < 4 ? (
          <Button onClick={handleNext} className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
            Siguiente
          </Button>
        ) : (
          <Button onClick={handleSubmit} className="bg-[#22C55E] hover:bg-green-600">
            <Save className="w-4 h-4 mr-2" />
            Crear Plan
          </Button>
        )}
      </div>
    </div>
  );
}

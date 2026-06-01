import { useState } from "react";
import { useNavigate } from "react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { ArrowLeft, Save } from "lucide-react";
import { Link } from "react-router";
import { toast } from "sonner";

export default function CreateProject() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    tutor: "",
    startDate: "",
    endDate: ""
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success("Proyecto creado exitosamente");
    setTimeout(() => navigate("/dashboard/projects"), 1000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/dashboard/projects">
          <Button variant="outline" size="icon">
            <ArrowLeft className="w-4 h-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Nuevo Proyecto</h1>
          <p className="text-muted-foreground">Crea un nuevo proyecto de titulación</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Información del Proyecto</CardTitle>
            <CardDescription>Completa los datos básicos del proyecto</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nombre del Proyecto *</Label>
              <Input
                id="name"
                placeholder="Ej: Sistema de Gestión Académica"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Descripción *</Label>
              <Textarea
                id="description"
                placeholder="Descripción detallada del proyecto..."
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                required
              />
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="tutor">Tutor Asignado</Label>
                <Select value={formData.tutor} onValueChange={(v) => setFormData({...formData, tutor: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar tutor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="tutor1">Dr. María González</SelectItem>
                    <SelectItem value="tutor2">Ing. Carlos Ramírez</SelectItem>
                    <SelectItem value="tutor3">Dra. Ana Silva</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="startDate">Fecha de Inicio</Label>
                <Input
                  id="startDate"
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => setFormData({...formData, startDate: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="endDate">Fecha de Finalización</Label>
              <Input
                id="endDate"
                type="date"
                value={formData.endDate}
                onChange={(e) => setFormData({...formData, endDate: e.target.value})}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3 mt-6">
          <Link to="/dashboard/projects">
            <Button variant="outline">Cancelar</Button>
          </Link>
          <Button type="submit" className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
            <Save className="w-4 h-4 mr-2" />
            Crear Proyecto
          </Button>
        </div>
      </form>
    </div>
  );
}

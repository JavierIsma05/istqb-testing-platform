import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { FlaskConical, Mail, Lock, User, ArrowLeft, Building2 } from "lucide-react";
import { toast } from "sonner";

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    institution: "",
    password: "",
    confirmPassword: "",
    role: ""
  });

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.fullName || !formData.email || !formData.password || !formData.role) {
      toast.error("Por favor completa todos los campos obligatorios");
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      toast.error("Las contraseñas no coinciden");
      return;
    }

    toast.success("¡Cuenta creada exitosamente!");
    setTimeout(() => {
      navigate("/login");
    }, 1500);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Side - Illustration */}
      <div className="hidden lg:flex items-center justify-center bg-gradient-to-br from-[#4B6B88] to-[#1E3A5F] p-12">
        <div className="max-w-md space-y-8 text-white">
          <div className="space-y-4">
            <h2 className="text-4xl font-bold">Únete a ISTQB Platform</h2>
            <p className="text-lg text-white/80">
              Crea tu cuenta y comienza a gestionar proyectos de pruebas de manera profesional
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6 space-y-4">
            <h3 className="font-semibold text-lg">¿Qué obtienes?</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-[#7DD3FC] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#1E3A5F]">✓</span>
                </div>
                <span className="text-white/90">Gestión completa del ciclo de vida ISTQB</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-[#7DD3FC] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#1E3A5F]">✓</span>
                </div>
                <span className="text-white/90">Trazabilidad entre requisitos y defectos</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-[#7DD3FC] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#1E3A5F]">✓</span>
                </div>
                <span className="text-white/90">Generación de informes profesionales PDF</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-[#7DD3FC] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#1E3A5F]">✓</span>
                </div>
                <span className="text-white/90">Métricas y monitoreo en tiempo real</span>
              </li>
              <li className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-[#7DD3FC] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-xs font-bold text-[#1E3A5F]">✓</span>
                </div>
                <span className="text-white/90">Colaboración tutor-estudiante</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8">
              <ArrowLeft className="w-4 h-4" />
              Volver al inicio
            </Link>
            <div className="w-16 h-16 mx-auto rounded-xl bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center mb-4">
              <FlaskConical className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-[#1E3A5F]">Crear Cuenta</h1>
            <p className="text-muted-foreground mt-2">Regístrate en ISTQB Platform</p>
          </div>

          <Card className="border-[#E0F2FE]">
            <CardHeader>
              <CardTitle>Registro</CardTitle>
              <CardDescription>Completa los datos para crear tu cuenta</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Nombre Completo *</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="fullName"
                      type="text"
                      placeholder="Juan Pérez García"
                      value={formData.fullName}
                      onChange={(e) => handleChange("fullName", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Correo Institucional *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="estudiante@universidad.edu"
                      value={formData.email}
                      onChange={(e) => handleChange("email", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="institution">Institución</Label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="institution"
                      type="text"
                      placeholder="Universidad Técnica"
                      value={formData.institution}
                      onChange={(e) => handleChange("institution", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Rol *</Label>
                  <Select value={formData.role} onValueChange={(value) => handleChange("role", value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona tu rol" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="student">Estudiante</SelectItem>
                      <SelectItem value="tutor">Tutor/Docente</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => handleChange("password", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirmar Contraseña *</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="••••••••"
                      value={formData.confirmPassword}
                      onChange={(e) => handleChange("confirmPassword", e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="flex items-start gap-2 text-sm">
                  <input type="checkbox" className="rounded border-[#4B6B88] mt-1" required />
                  <span className="text-muted-foreground">
                    Acepto los términos y condiciones y la política de privacidad
                  </span>
                </div>

                <Button type="submit" className="w-full bg-[#4B6B88] hover:bg-[#1E3A5F]">
                  Crear Cuenta
                </Button>
              </form>

              <div className="mt-6 text-center text-sm">
                <span className="text-muted-foreground">¿Ya tienes cuenta? </span>
                <Link to="/login" className="text-[#4B6B88] hover:underline font-medium">
                  Inicia sesión
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

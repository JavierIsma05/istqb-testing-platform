import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { FlaskConical, Mail, Lock, LogIn, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password || !role) {
      toast.error("Por favor completa todos los campos");
      return;
    }

    toast.success("¡Inicio de sesión exitoso!");
    
    // Redirect based on role
    setTimeout(() => {
      switch (role) {
        case "student":
          navigate("/dashboard/student");
          break;
        case "tutor":
          navigate("/dashboard/tutor");
          break;
        case "admin":
          navigate("/dashboard/admin");
          break;
        default:
          navigate("/dashboard/student");
      }
    }, 1000);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Side - Form */}
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
            <h1 className="text-3xl font-bold text-[#1E3A5F]">Bienvenido de vuelta</h1>
            <p className="text-muted-foreground mt-2">Ingresa a tu cuenta para continuar</p>
          </div>

          <Card className="border-[#E0F2FE]">
            <CardHeader>
              <CardTitle>Iniciar Sesión</CardTitle>
              <CardDescription>Accede a la plataforma ISTQB</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Correo Institucional</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="estudiante@universidad.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Rol</Label>
                  <Select value={role} onValueChange={setRole}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona tu rol" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="student">Estudiante</SelectItem>
                      <SelectItem value="tutor">Tutor/Docente</SelectItem>
                      <SelectItem value="admin">Administrador</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded border-[#4B6B88]" />
                    <span className="text-muted-foreground">Recordarme</span>
                  </label>
                  <Link to="/forgot-password" className="text-[#4B6B88] hover:underline">
                    ¿Olvidaste tu contraseña?
                  </Link>
                </div>

                <Button type="submit" className="w-full bg-[#4B6B88] hover:bg-[#1E3A5F]">
                  <LogIn className="w-4 h-4 mr-2" />
                  Iniciar Sesión
                </Button>
              </form>

              <div className="mt-6 text-center text-sm">
                <span className="text-muted-foreground">¿No tienes cuenta? </span>
                <Link to="/register" className="text-[#4B6B88] hover:underline font-medium">
                  Regístrate aquí
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Right Side - Illustration */}
      <div className="hidden lg:flex items-center justify-center bg-gradient-to-br from-[#4B6B88] to-[#1E3A5F] p-12">
        <div className="max-w-md space-y-8 text-white">
          <div className="space-y-4">
            <h2 className="text-4xl font-bold">Gestión Profesional de Pruebas</h2>
            <p className="text-lg text-white/80">
              Plataforma completa para gestionar el ciclo de vida de pruebas según estándares ISTQB
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="w-8 h-8 rounded-lg bg-[#7DD3FC] flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-[#1E3A5F]">✓</span>
              </div>
              <div>
                <h3 className="font-semibold">Estándares Internacionales</h3>
                <p className="text-sm text-white/70">Cumple con ISTQB e ISO/IEC/IEEE 29119</p>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="w-8 h-8 rounded-lg bg-[#7DD3FC] flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-[#1E3A5F]">✓</span>
              </div>
              <div>
                <h3 className="font-semibold">Trazabilidad Completa</h3>
                <p className="text-sm text-white/70">Desde requisitos hasta defectos</p>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-white/10 backdrop-blur-sm rounded-lg p-4">
              <div className="w-8 h-8 rounded-lg bg-[#7DD3FC] flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-bold text-[#1E3A5F]">✓</span>
              </div>
              <div>
                <h3 className="font-semibold">Informes Profesionales</h3>
                <p className="text-sm text-white/70">Genera reportes PDF institucionales</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 pt-8 border-t border-white/20">
            <div className="text-center">
              <p className="text-3xl font-bold text-[#7DD3FC]">6</p>
              <p className="text-sm text-white/70">Fases</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-[#7DD3FC]">100%</p>
              <p className="text-sm text-white/70">ISTQB</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-[#7DD3FC]">24/7</p>
              <p className="text-sm text-white/70">Acceso</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

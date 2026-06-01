import { useState } from "react";
import { Link } from "react-router";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { FlaskConical, Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { toast } from "sonner";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      toast.error("Por favor ingresa tu correo electrónico");
      return;
    }

    toast.success("Correo enviado exitosamente");
    setEmailSent(true);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-[#F5F7FA] to-white">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/login" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6">
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>
          <div className="w-16 h-16 mx-auto rounded-xl bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center mb-4">
            <FlaskConical className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-[#1E3A5F]">Recuperar Contraseña</h1>
          <p className="text-muted-foreground mt-2">
            Te enviaremos un enlace para restablecer tu contraseña
          </p>
        </div>

        <Card className="border-[#E0F2FE]">
          <CardHeader>
            <CardTitle>Restablecer Contraseña</CardTitle>
            <CardDescription>
              Ingresa tu correo institucional para continuar
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!emailSent ? (
              <form onSubmit={handleSubmit} className="space-y-4">
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

                <Button type="submit" className="w-full bg-[#4B6B88] hover:bg-[#1E3A5F]">
                  Enviar Enlace de Recuperación
                </Button>
              </form>
            ) : (
              <div className="text-center space-y-4 py-6">
                <div className="w-16 h-16 mx-auto rounded-full bg-[#E0F2FE] flex items-center justify-center">
                  <CheckCircle className="w-8 h-8 text-[#22C55E]" />
                </div>
                <div className="space-y-2">
                  <h3 className="font-semibold text-lg">¡Correo Enviado!</h3>
                  <p className="text-sm text-muted-foreground">
                    Hemos enviado un enlace de recuperación a <strong>{email}</strong>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Por favor revisa tu bandeja de entrada y sigue las instrucciones.
                  </p>
                </div>
                <div className="pt-4">
                  <Link to="/login">
                    <Button variant="outline" className="w-full">
                      Volver al inicio de sesión
                    </Button>
                  </Link>
                </div>
              </div>
            )}

            {!emailSent && (
              <div className="mt-6 text-center text-sm">
                <span className="text-muted-foreground">¿Recordaste tu contraseña? </span>
                <Link to="/login" className="text-[#4B6B88] hover:underline font-medium">
                  Inicia sesión
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

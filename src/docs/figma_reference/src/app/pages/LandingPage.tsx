import { Link } from "react-router";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { 
  FlaskConical, 
  FileCheck, 
  Bug, 
  BarChart3, 
  Shield, 
  Workflow,
  CheckCircle2,
  TrendingUp,
  Users,
  Target,
  Zap,
  Award
} from "lucide-react";

export default function LandingPage() {
  const features = [
    {
      icon: <Workflow className="w-8 h-8" />,
      title: "Gestión Completa del Ciclo ISTQB",
      description: "Gestiona todo el ciclo de vida de pruebas según estándares ISTQB e ISO/IEC/IEEE 29119",
      color: "text-[#4B6B88]"
    },
    {
      icon: <FileCheck className="w-8 h-8" />,
      title: "Plan de Pruebas",
      description: "Crea y administra planes de prueba profesionales con criterios de entrada y salida",
      color: "text-[#7DD3FC]"
    },
    {
      icon: <FlaskConical className="w-8 h-8" />,
      title: "Casos de Prueba",
      description: "Diseña casos de prueba con técnicas de caja negra, blanca, partición de equivalencia y más",
      color: "text-[#22C55E]"
    },
    {
      icon: <Bug className="w-8 h-8" />,
      title: "Gestión de Defectos",
      description: "Registra y da seguimiento a defectos con ciclo de vida completo y trazabilidad",
      color: "text-[#EF4444]"
    },
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: "Monitoreo y Métricas",
      description: "Visualiza KPIs, cobertura, densidad de defectos y progreso en tiempo real",
      color: "text-[#FACC15]"
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: "Trazabilidad Total",
      description: "Matriz de trazabilidad completa entre requisitos, casos de prueba y defectos",
      color: "text-[#4B6B88]"
    }
  ];

  const stats = [
    { value: "100%", label: "ISTQB Compliant" },
    { value: "6", label: "Fases del Ciclo" },
    { value: "3", label: "Roles de Usuario" },
    { value: "∞", label: "Proyectos" }
  ];

  const phases = [
    { number: "01", name: "Planificación", description: "Define estrategia y recursos" },
    { number: "02", name: "Análisis", description: "Analiza requisitos y riesgos" },
    { number: "03", name: "Diseño", description: "Diseña casos de prueba" },
    { number: "04", name: "Implementación", description: "Prepara entorno de pruebas" },
    { number: "05", name: "Ejecución", description: "Ejecuta casos y registra resultados" },
    { number: "06", name: "Cierre", description: "Genera informes y lecciones aprendidas" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-[#F5F7FA]">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-border">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center">
                <FlaskConical className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[#1E3A5F]">ISTQB Platform</h1>
                <p className="text-xs text-muted-foreground">Testing Lifecycle Management</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link to="/register">
                <Button variant="ghost">Registrarse</Button>
              </Link>
              <Link to="/login">
                <Button className="bg-[#4B6B88] hover:bg-[#1E3A5F]">Iniciar Sesión</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <Badge className="bg-[#E0F2FE] text-[#1E3A5F] hover:bg-[#E0F2FE]">
              <Award className="w-3 h-3 mr-1" />
              Certificado ISTQB & ISO/IEC/IEEE 29119
            </Badge>
            <h1 className="text-5xl font-bold text-[#1E3A5F] leading-tight">
              Gestiona el Ciclo de Vida de Pruebas de forma{" "}
              <span className="text-[#4B6B88]">Profesional</span>
            </h1>
            <p className="text-lg text-muted-foreground">
              Plataforma académica SaaS para gestionar proyectos de titulación universitarios 
              basados en estándares internacionales de pruebas de software ISTQB.
            </p>
            <div className="flex gap-4">
              <Link to="/register">
                <Button size="lg" className="bg-[#4B6B88] hover:bg-[#1E3A5F]">
                  <Zap className="w-4 h-4 mr-2" />
                  Comenzar Ahora
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline">
                  Ver Demo
                </Button>
              </Link>
            </div>
          </div>
          <div className="relative">
            <div className="bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] rounded-2xl p-8 shadow-2xl">
              <div className="bg-white rounded-lg p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-[#1E3A5F]">Estado del Proyecto</h3>
                  <Badge className="bg-[#22C55E] text-white">Activo</Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Cobertura</span>
                    <span className="font-semibold text-[#4B6B88]">87%</span>
                  </div>
                  <div className="w-full h-2 bg-[#E0F2FE] rounded-full overflow-hidden">
                    <div className="h-full bg-[#4B6B88] rounded-full" style={{ width: "87%" }}></div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 pt-4">
                  <div>
                    <p className="text-2xl font-bold text-[#4B6B88]">24</p>
                    <p className="text-xs text-muted-foreground">Casos</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-[#22C55E]">18</p>
                    <p className="text-xs text-muted-foreground">Passed</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-[#EF4444]">3</p>
                    <p className="text-xs text-muted-foreground">Defects</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="container mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <Card key={index} className="text-center border-[#E0F2FE]">
              <CardContent className="pt-6">
                <p className="text-4xl font-bold text-[#4B6B88] mb-2">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <Badge className="bg-[#E0F2FE] text-[#1E3A5F] hover:bg-[#E0F2FE] mb-4">
            Funcionalidades
          </Badge>
          <h2 className="text-4xl font-bold text-[#1E3A5F] mb-4">
            Todo lo que necesitas para gestionar pruebas
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Una plataforma completa con todas las herramientas para gestionar el ciclo de vida 
            de pruebas según estándares internacionales
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="border-[#E0F2FE] hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className={`${feature.color} mb-3`}>
                  {feature.icon}
                </div>
                <CardTitle className="text-[#1E3A5F]">{feature.title}</CardTitle>
                <CardDescription>{feature.description}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      {/* Timeline ISTQB */}
      <section className="bg-gradient-to-br from-[#4B6B88] to-[#1E3A5F] py-20">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <Badge className="bg-white/20 text-white hover:bg-white/20 mb-4">
              Ciclo de Vida ISTQB
            </Badge>
            <h2 className="text-4xl font-bold text-white mb-4">
              6 Fases del Testing Profesional
            </h2>
            <p className="text-lg text-white/80 max-w-2xl mx-auto">
              Gestiona cada fase del ciclo de vida de pruebas de manera estructurada y profesional
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {phases.map((phase, index) => (
              <div key={index} className="bg-white/10 backdrop-blur-sm rounded-lg p-6 border border-white/20">
                <div className="flex items-start gap-4">
                  <div className="text-4xl font-bold text-[#7DD3FC]">{phase.number}</div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">{phase.name}</h3>
                    <p className="text-white/70">{phase.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-20">
        <Card className="bg-gradient-to-r from-[#4B6B88] to-[#7DD3FC] border-0 text-white">
          <CardContent className="p-12 text-center">
            <Target className="w-16 h-16 mx-auto mb-6 text-white" />
            <h2 className="text-3xl font-bold mb-4">
              ¿Listo para gestionar tus pruebas profesionalmente?
            </h2>
            <p className="text-lg text-white/90 mb-8 max-w-2xl mx-auto">
              Únete a estudiantes y profesores que ya están utilizando ISTQB Platform 
              para gestionar sus proyectos de titulación
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/register">
                <Button size="lg" variant="secondary">
                  Crear Cuenta Gratis
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline" className="bg-white/10 border-white text-white hover:bg-white/20">
                  Iniciar Sesión
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="bg-[#1E3A5F] text-white py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center">
                  <FlaskConical className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold">ISTQB Platform</span>
              </div>
              <p className="text-sm text-white/70">
                Plataforma profesional para gestión de pruebas académicas
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Producto</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>Funcionalidades</li>
                <li>Precios</li>
                <li>Seguridad</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Recursos</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>Documentación</li>
                <li>Tutoriales</li>
                <li>Soporte</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Estándares</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li>ISTQB Foundation</li>
                <li>ISO/IEC/IEEE 29119</li>
                <li>Best Practices</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-sm text-white/70">
            <p>© 2026 ISTQB Testing Lifecycle Platform. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

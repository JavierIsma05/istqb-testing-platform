import { useState } from "react";
import { Outlet, Link, useLocation } from "react-router";
import { Button } from "../components/ui/button";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Badge } from "../components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  FlaskConical,
  LayoutDashboard,
  FolderKanban,
  FileText,
  ClipboardList,
  AlertTriangle,
  TestTube,
  Play,
  Bug,
  GitBranch,
  BarChart3,
  FileBarChart,
  Workflow,
  Bell,
  Settings,
  User,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  Shield,
  Moon,
  Sun
} from "lucide-react";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: "Dashboard", href: "/dashboard/student", icon: LayoutDashboard },
    { name: "Proyectos", href: "/dashboard/projects", icon: FolderKanban },
    { name: "Requisitos", href: "/dashboard/requirements", icon: FileText },
    { name: "Plan de Pruebas", href: "/dashboard/test-plans", icon: ClipboardList },
    { name: "Incidencias", href: "/dashboard/incidents", icon: AlertTriangle },
    { name: "Casos de Prueba", href: "/dashboard/test-cases", icon: TestTube },
    { name: "Ejecución", href: "/dashboard/test-execution", icon: Play },
    { name: "Defectos", href: "/dashboard/defects", icon: Bug },
    { name: "Trazabilidad", href: "/dashboard/traceability", icon: GitBranch },
    { name: "Monitorización", href: "/dashboard/monitoring", icon: BarChart3 },
    { name: "Informes", href: "/dashboard/reports", icon: FileBarChart },
    { name: "Fases ISTQB", href: "/dashboard/phases", icon: Workflow },
  ];

  const isActive = (href: string) => {
    return location.pathname === href;
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen bg-[#F5F7FA] ${darkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-40 h-screen bg-white border-r border-border transition-all duration-300 ${
          sidebarOpen ? "w-64" : "w-20"
        } ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            {sidebarOpen ? (
              <Link to="/" className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center">
                  <FlaskConical className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="font-bold text-[#1E3A5F]">ISTQB Platform</h1>
                  <p className="text-xs text-muted-foreground">Testing Lifecycle</p>
                </div>
              </Link>
            ) : (
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#4B6B88] to-[#7DD3FC] flex items-center justify-center mx-auto">
                <FlaskConical className="w-6 h-6 text-white" />
              </div>
            )}
            {sidebarOpen && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(false)}
                className="hidden lg:flex"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    active
                      ? "bg-[#E0F2FE] text-[#4B6B88]"
                      : "text-muted-foreground hover:bg-[#F5F7FA] hover:text-foreground"
                  } ${!sidebarOpen ? "justify-center" : ""}`}
                  title={!sidebarOpen ? item.name : undefined}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm">{item.name}</span>}
                </Link>
              );
            })}
          </nav>

          {/* Collapse Button */}
          {!sidebarOpen && (
            <div className="p-4 border-t border-border">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSidebarOpen(true)}
                className="w-full"
              >
                <Menu className="w-5 h-5" />
              </Button>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <div
        className={`transition-all duration-300 ${
          sidebarOpen ? "lg:ml-64" : "lg:ml-20"
        }`}
      >
        {/* Top Navbar */}
        <header className="sticky top-0 z-30 bg-white border-b border-border">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </Button>
              <div>
                <h2 className="text-lg font-semibold text-[#1E3A5F]">Sistema de Gestión de Pruebas</h2>
                <p className="text-sm text-muted-foreground">Plataforma ISTQB</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Dark Mode Toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleDarkMode}
                title={darkMode ? "Modo claro" : "Modo oscuro"}
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </Button>

              {/* Notifications */}
              <Link to="/dashboard/notifications">
                <Button variant="ghost" size="icon" className="relative">
                  <Bell className="w-5 h-5" />
                  <span className="absolute top-2 right-2 w-2 h-2 bg-[#EF4444] rounded-full"></span>
                </Button>
              </Link>

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-3 pl-2">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-[#4B6B88] text-white">JP</AvatarFallback>
                    </Avatar>
                    <div className="hidden md:block text-left">
                      <p className="text-sm font-medium">Juan Pérez</p>
                      <p className="text-xs text-muted-foreground">Estudiante</p>
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">Juan Pérez García</p>
                      <p className="text-xs text-muted-foreground">estudiante@uni.edu</p>
                      <Badge className="w-fit mt-1 bg-[#E0F2FE] text-[#4B6B88]">Estudiante</Badge>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard/profile" className="cursor-pointer">
                      <User className="w-4 h-4 mr-2" />
                      Mi Perfil
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard/settings" className="cursor-pointer">
                      <Settings className="w-4 h-4 mr-2" />
                      Configuración
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/dashboard/admin" className="cursor-pointer">
                      <Shield className="w-4 h-4 mr-2" />
                      Panel Admin
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/login" className="cursor-pointer text-[#EF4444]">
                      <LogOut className="w-4 h-4 mr-2" />
                      Cerrar Sesión
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
    </div>
  );
}

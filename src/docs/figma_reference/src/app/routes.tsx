import { createBrowserRouter } from "react-router";
import LandingPage from "./pages/LandingPage";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ForgotPassword from "./pages/auth/ForgotPassword";
import DashboardLayout from "./layouts/DashboardLayout";
import StudentDashboard from "./pages/dashboard/StudentDashboard";
import TutorDashboard from "./pages/dashboard/TutorDashboard";
import AdminDashboard from "./pages/dashboard/AdminDashboard";
import ProjectsList from "./pages/projects/ProjectsList";
import ProjectDetail from "./pages/projects/ProjectDetail";
import CreateProject from "./pages/projects/CreateProject";
import RequirementsList from "./pages/requirements/RequirementsList";
import TestPlanList from "./pages/test-plan/TestPlanList";
import CreateTestPlan from "./pages/test-plan/CreateTestPlan";
import IncidentsList from "./pages/incidents/IncidentsList";
import TestCasesList from "./pages/test-cases/TestCasesList";
import TestExecution from "./pages/test-execution/TestExecution";
import DefectsList from "./pages/defects/DefectsList";
import Traceability from "./pages/traceability/Traceability";
import Monitoring from "./pages/monitoring/Monitoring";
import Reports from "./pages/reports/Reports";
import PhasesManagement from "./pages/phases/PhasesManagement";
import Notifications from "./pages/notifications/Notifications";
import Profile from "./pages/profile/Profile";
import Settings from "./pages/settings/Settings";
import AdminPanel from "./pages/admin/AdminPanel";
import NotFound from "./pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: LandingPage,
  },
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/register",
    Component: Register,
  },
  {
    path: "/forgot-password",
    Component: ForgotPassword,
  },
  {
    path: "/dashboard",
    Component: DashboardLayout,
    children: [
      {
        path: "student",
        Component: StudentDashboard,
      },
      {
        path: "tutor",
        Component: TutorDashboard,
      },
      {
        path: "admin",
        Component: AdminDashboard,
      },
      {
        path: "projects",
        Component: ProjectsList,
      },
      {
        path: "projects/create",
        Component: CreateProject,
      },
      {
        path: "projects/:id",
        Component: ProjectDetail,
      },
      {
        path: "requirements",
        Component: RequirementsList,
      },
      {
        path: "test-plans",
        Component: TestPlanList,
      },
      {
        path: "test-plans/create",
        Component: CreateTestPlan,
      },
      {
        path: "incidents",
        Component: IncidentsList,
      },
      {
        path: "test-cases",
        Component: TestCasesList,
      },
      {
        path: "test-execution",
        Component: TestExecution,
      },
      {
        path: "defects",
        Component: DefectsList,
      },
      {
        path: "traceability",
        Component: Traceability,
      },
      {
        path: "monitoring",
        Component: Monitoring,
      },
      {
        path: "reports",
        Component: Reports,
      },
      {
        path: "phases",
        Component: PhasesManagement,
      },
      {
        path: "notifications",
        Component: Notifications,
      },
      {
        path: "profile",
        Component: Profile,
      },
      {
        path: "settings",
        Component: Settings,
      },
      {
        path: "admin",
        Component: AdminPanel,
      },
    ],
  },
  {
    path: "*",
    Component: NotFound,
  },
]);

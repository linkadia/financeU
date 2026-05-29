import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Learn from "./pages/Learn";
import Profile from "./pages/Profile";
import OnboardingStep1 from "./pages/onboarding/OnboardingStep1";
import OnboardingStep2 from "./pages/onboarding/OnboardingStep2";
import OnboardingStep3 from "./pages/onboarding/OnboardingStep3";
import SelectAgent from "./pages/onboarding/SelectAgent";
import { getCurrentUser } from "./utils/session";

function OnboardingRoute({ children }) {
  const currentUser = getCurrentUser();

  if (!currentUser?.id) {
    return <Navigate to="/" replace />;
  }

  if (currentUser.onboarding_completed) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/onboarding/step1" element={<OnboardingRoute><SelectAgent /></OnboardingRoute>} />
      <Route path="/onboarding/step2" element={<OnboardingRoute><OnboardingStep1 /></OnboardingRoute>} />
      <Route path="/onboarding/step3" element={<OnboardingRoute><OnboardingStep2 /></OnboardingRoute>} />
      <Route path="/onboarding/step4" element={<OnboardingRoute><OnboardingStep3 /></OnboardingRoute>} />
      <Route path="/onboarding/select-agent" element={<Navigate to="/onboarding/step1" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/learn" element={<Learn />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import MarketsPage from "./pages/MarketsPage";
import LearnPage from "./pages/LearnPage";
import ProfilePage from "./pages/ProfilePage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

// New Stitch screens
import Dashboard from "./pages/Dashboard";
import Learn from "./pages/Learn";
import Profile from "./pages/Profile";

// Onboarding
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
      {/* ── Onboarding flow (no layout wrapper, full-screen) ── */}
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/onboarding/step1" element={<OnboardingRoute><SelectAgent /></OnboardingRoute>} />
      <Route path="/onboarding/step2" element={<OnboardingRoute><OnboardingStep1 /></OnboardingRoute>} />
      <Route path="/onboarding/step3" element={<OnboardingRoute><OnboardingStep2 /></OnboardingRoute>} />
      <Route path="/onboarding/step4" element={<OnboardingRoute><OnboardingStep3 /></OnboardingRoute>} />
      <Route path="/onboarding/select-agent" element={<Navigate to="/onboarding/step1" replace />} />

      {/* ── Auth ── */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/stitch-test" element={<Login />} />

      {/* ── Main app (Stitch screens, standalone) ── */}
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/learn" element={<Learn />} />
      <Route path="/profile" element={<Profile />} />

      {/* ── Legacy routes (keeping existing pages intact) ── */}
      <Route element={<MainLayout />}>
        <Route path="/home" element={<HomePage />} />
        <Route path="/markets" element={<MarketsPage />} />
        <Route path="/learn-old" element={<LearnPage />} />
        <Route path="/profile-old" element={<ProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

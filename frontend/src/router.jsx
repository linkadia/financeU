import { Routes, Route, Navigate } from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import LoginPage from "./pages/LoginPage";
import HomePage from "./pages/HomePage";
import MarketsPage from "./pages/MarketsPage";
import LearnPage from "./pages/LearnPage";
import ProfilePage from "./pages/ProfilePage";

// New Stitch screens
import Dashboard from "./pages/Dashboard";
import Learn from "./pages/Learn";
import Profile from "./pages/Profile";

// Onboarding
import OnboardingStep1 from "./pages/onboarding/OnboardingStep1";
import OnboardingStep2 from "./pages/onboarding/OnboardingStep2";
import OnboardingStep3 from "./pages/onboarding/OnboardingStep3";
import OnboardingStep4 from "./pages/onboarding/OnboardingStep4";
import SelectAgent from "./pages/onboarding/SelectAgent";

export default function AppRouter() {
  return (
    <Routes>
      {/* ── Onboarding flow (no layout wrapper, full-screen) ── */}
      <Route path="/" element={<OnboardingStep1 />} />
      <Route path="/onboarding/step1" element={<OnboardingStep1 />} />
      <Route path="/onboarding/step2" element={<OnboardingStep2 />} />
      <Route path="/onboarding/step3" element={<OnboardingStep3 />} />
      <Route path="/onboarding/step4" element={<OnboardingStep4 />} />
      <Route path="/onboarding/select-agent" element={<SelectAgent />} />

      {/* ── Auth ── */}
      <Route path="/login" element={<LoginPage />} />

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


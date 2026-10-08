import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Learn from "./pages/Learn";
import Profile from "./pages/Profile";
import OnboardingStep1 from "./pages/onboarding/OnboardingStep1";
import OnboardingStep2 from "./pages/onboarding/OnboardingStep2";
import OnboardingStep3 from "./pages/onboarding/OnboardingStep3";
import SelectAgent from "./pages/onboarding/SelectAgent";
import Privacy from "./pages/Privacy";
import { clearCurrentUser, getCurrentUser, setCurrentUser } from "./utils/session";
import { getSubscriptionStatus } from "./api/users";

function SubscriptionRoute({ children }) {
  const [userId] = useState(() => getCurrentUser()?.id);
  const [access, setAccess] = useState(userId ? 'checking' : 'blocked');

  useEffect(() => {
    if (!userId) return undefined;
    let disposed = false;
    let checking = false;
    async function checkAccess() {
      if (checking) return;
      checking = true;
      try {
        const subscription = await getSubscriptionStatus(userId);
        if (disposed) return;
        const user = getCurrentUser();
        if (!subscription.can_access || user?.id !== userId) {
          clearCurrentUser();
          setAccess('blocked');
        } else {
          setCurrentUser({ ...user, ...subscription });
          setAccess('allowed');
        }
      } catch (error) {
        if (!disposed) setAccess('checking');
      } finally {
        checking = false;
      }
    }
    checkAccess();
    const interval = window.setInterval(checkAccess, 60000);
    window.addEventListener('focus', checkAccess);
    return () => {
      disposed = true;
      window.clearInterval(interval);
      window.removeEventListener('focus', checkAccess);
    };
  }, [userId]);

  if (access === 'blocked') return <Navigate to="/" replace />;
  if (access === 'checking') return <div role="status" aria-busy="true">…</div>;
  return children;
}

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
      <Route path="/onboarding/step1" element={<SubscriptionRoute><OnboardingRoute><SelectAgent /></OnboardingRoute></SubscriptionRoute>} />
      <Route path="/onboarding/step2" element={<SubscriptionRoute><OnboardingRoute><OnboardingStep1 /></OnboardingRoute></SubscriptionRoute>} />
      <Route path="/onboarding/step3" element={<SubscriptionRoute><OnboardingRoute><OnboardingStep2 /></OnboardingRoute></SubscriptionRoute>} />
      <Route path="/onboarding/step4" element={<SubscriptionRoute><OnboardingRoute><OnboardingStep3 /></OnboardingRoute></SubscriptionRoute>} />
      <Route path="/onboarding/select-agent" element={<Navigate to="/onboarding/step1" replace />} />
      <Route path="/dashboard" element={<SubscriptionRoute><Dashboard /></SubscriptionRoute>} />
      <Route path="/learn" element={<SubscriptionRoute><Learn /></SubscriptionRoute>} />
      <Route path="/profile" element={<SubscriptionRoute><Profile /></SubscriptionRoute>} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

import AppRouter from "./router";
import ScrollToTop from "./components/common/ScrollToTop";
import CookieBanner from "./components/privacy/CookieBanner";
import { CookieConsentProvider } from "./context/CookieConsentContext";
import './privacy.css';

export default function App() {
  return (
    <CookieConsentProvider>
      <ScrollToTop />
      <AppRouter />
      <CookieBanner />
    </CookieConsentProvider>
  );
}

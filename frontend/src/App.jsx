import AppRouter from "./router";
import ScrollToTop from "./components/common/ScrollToTop";
import CookieBanner from "./components/privacy/CookieBanner";

export default function App() {
  return (
    <>
      <ScrollToTop />
      <AppRouter />
      <CookieBanner />
    </>
  );
}

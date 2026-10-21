import { useLayoutEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function ScrollToTop() {
  const { pathname, hash, key } = useLocation();

  useLayoutEffect(() => {
    if (hash) {
      let id;
      try { id = decodeURIComponent(hash.slice(1)); } catch { id = hash.slice(1); }
      const target = document.getElementById(id);
      if (target) {
        target.scrollIntoView({ behavior: 'instant', block: 'start' });
        target.focus({ preventScroll: true });
        return;
      }
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;

    document.querySelectorAll('[data-scroll-root]').forEach((element) => {
      element.scrollTop = 0;
      element.scrollLeft = 0;
    });
  }, [pathname, hash, key]);

  return null;
}

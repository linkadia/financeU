import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

function gtmPlugin(gtmId) {
  const hasGtmId = Boolean(gtmId);

  return {
    name: "financu-gtm",
    transformIndexHtml(html) {
      if (!hasGtmId) {
        return html
          .replace("<!-- FINANCU_GTM_HEAD -->", "")
          .replace("<!-- FINANCU_GTM_NOSCRIPT -->", "");
      }

      const escapedGtmId = JSON.stringify(gtmId);
      const headSnippet = `<script>
        (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
        new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        })(window,document,'script','dataLayer',${escapedGtmId});
      </script>`;
      const noScript = `<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=${encodeURIComponent(gtmId)}" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>`;

      return html
        .replace("<!-- FINANCU_GTM_HEAD -->", headSnippet)
        .replace("<!-- FINANCU_GTM_NOSCRIPT -->", noScript);
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react(), gtmPlugin(env.VITE_GTM_ID?.trim())],
  };
});

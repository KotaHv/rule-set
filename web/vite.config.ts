import { createReadStream, statSync } from "node:fs";
import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const RULE_SET_DIR = path.resolve(import.meta.dirname, "../rule-set");

function serveRuleSet(): Plugin {
  return {
    name: "serve-rule-set",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        if (request.method !== "GET" && request.method !== "HEAD") {
          next();
          return;
        }

        let filepath: string;
        try {
          const pathname = decodeURIComponent(
            new URL(request.url ?? "/", "http://localhost").pathname,
          );
          filepath = path.join(RULE_SET_DIR, pathname);
        } catch {
          next();
          return;
        }

        if (!filepath.startsWith(`${RULE_SET_DIR}${path.sep}`)) {
          next();
          return;
        }

        try {
          if (!statSync(filepath).isFile()) {
            next();
            return;
          }
        } catch {
          next();
          return;
        }

        response.setHeader("Content-Type", "application/octet-stream");
        createReadStream(filepath).pipe(response);
      });
    },
  };
}

export default defineConfig(({ command, isPreview }) => ({
  base:
    process.env.VITE_BASE ??
    (command === "build" || isPreview ? "/rule-set/" : "/"),
  plugins: [react(), tailwindcss(), serveRuleSet()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
}));

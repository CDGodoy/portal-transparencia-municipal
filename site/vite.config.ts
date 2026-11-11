import { defineConfig } from "vite";

// Em GitHub Pages o site fica em /<repositorio>/; o workflow define VITE_BASE.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 900 },
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },


  // ── Production Build Optimizations ────────────────────────────────────────
  build: {
    // Vite 8 uses oxc (replaces esbuild) — drop console & debugger in prod
    minify: 'oxc',

    // Enable CSS code splitting — each async chunk gets its own CSS file
    cssCodeSplit: true,

    // Lower the warning threshold so we notice regressions sooner
    chunkSizeWarningLimit: 400,

    rollupOptions: {
      output: {
        // ── Smart Vendor Splitting ───────────────────────────────────────
        // Browsers can cache these chunks independently from app code.
        // When only app code changes, users re-download ONLY the app chunk.
        manualChunks(id: string) {
          // 1. React core runtime — changes almost never
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/scheduler/')) {
            return 'vendor-react';
          }

          // 2. React Router — routing layer, rarely updated
          if (id.includes('node_modules/react-router') ||
              id.includes('node_modules/@remix-run/')) {
            return 'vendor-router';
          }

          // 3. TanStack React Query — data-fetching layer
          if (id.includes('node_modules/@tanstack/')) {
            return 'vendor-query';
          }

          // 4. Recharts + d3 primitives — largest visual dependency
          if (id.includes('node_modules/recharts') ||
              id.includes('node_modules/d3-') ||
              id.includes('node_modules/victory-vendor')) {
            return 'vendor-charts';
          }

          // 5. Form / validation stack
          if (id.includes('node_modules/react-hook-form') ||
              id.includes('node_modules/@hookform/') ||
              id.includes('node_modules/zod')) {
            return 'vendor-forms';
          }

          // 6. Utility libraries (axios, date-fns, clsx, tailwind-merge, zustand)
          if (id.includes('node_modules/axios') ||
              id.includes('node_modules/date-fns') ||
              id.includes('node_modules/clsx') ||
              id.includes('node_modules/tailwind-merge') ||
              id.includes('node_modules/zustand') ||
              id.includes('node_modules/lucide-react') ||
              id.includes('node_modules/class-variance-authority') ||
              id.includes('node_modules/@radix-ui/')) {
            return 'vendor-utils';
          }
        },

        // Consistent file naming with content hash for long-term caching
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
});

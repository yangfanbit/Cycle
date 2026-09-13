import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

/**
 * Monorepo（ThreeC）：canonical Research Export 只有一份 —— 根 exports/timeline_export_v1.json。
 * 前端 Adapter 经 `@exports/*` alias 直接消费，不再维护 src/data/timeline/data/ 手工副本。
 * 见 docs/PROJECT_STATE.md「Export canonical source」与 contracts/timeline_export_v1.md。
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@exports': fileURLToPath(new URL('./exports', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'node',
  },
});

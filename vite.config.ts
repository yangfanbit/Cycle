import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

/**
 * Monorepo（ThreeC）：canonical Research Export 只有一份 —— 根 exports/timeline_export_v1.json。
 * 前端 Adapter 经 `@exports/*` alias 直接消费，不再维护 src/data/timeline/data/ 手工副本。
 * 见 docs/PROJECT_STATE.md「Export canonical source」与 contracts/timeline_export_v1.md。
 *
 * `@current` 指向 research/current/ —— Current Research Discovery 的**静态研究 Artifact**
 * （Phase 7）。同样是「Research 生成、Product 只读消费」：静态 import，无运行时网络请求。
 * 网络 / AI 只出现在研究数据生成端，不进入产品运行端。
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@exports': fileURLToPath(new URL('./exports', import.meta.url)),
      '@current': fileURLToPath(new URL('./research/current', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'node',
  },
});

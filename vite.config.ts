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
 *
 * `@observation` 指向 research/research/reports/ —— Time-based Observation Layer 的
 * **静态研究 Artifact**（Phase 7.2，`time_observation_patterns_v0_2.json`）。
 * 同样只读消费；该目录下的探索性脚本与中间结果**不是**产品依赖。
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@exports': fileURLToPath(new URL('./exports', import.meta.url)),
      '@current': fileURLToPath(new URL('./research/current', import.meta.url)),
      '@observation': fileURLToPath(new URL('./research/research/reports', import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: 'node',
  },
});

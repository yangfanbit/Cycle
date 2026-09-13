/**
 * 开发预览数据入口：Research 唯一 canonical 导出（timeline_export_v1，Canonical Contract v1.0）。
 *
 * Monorepo（ThreeC）边界：
 * - canonical export 只有一份：`<repo root>/exports/timeline_export_v1.json`
 *   （由 Research 流水线生成；经 vite alias `@exports` / tsconfig paths 直接消费）。
 * - **不再维护** Cycle 内手工副本（旧 `src/data/timeline/data/timeline_export_v1.json` 已移除）。
 *   若前端需要缓存，只能作为 build artifact，不得回退为手工维护的数据文件。
 * - 预览数据不是生产数据出口：不写入 data/verified、不混入 allCampaigns
 *   （由 timelineAdapter 测试断言保证）。
 * - 静态 import，无运行时网络请求（保持静态 PWA 不变）。
 *
 * 契约见 contracts/timeline_export_v1.md 与 docs/PROJECT_STATE.md。
 */
import timelineExportV1Json from '@exports/timeline_export_v1.json';
import type { TimelineExportV1 } from './timelineTypes';

/** Research canonical 导出数据（v1.0；经 timelineAdapter 校验后使用） */
export const timelineExportData = timelineExportV1Json as unknown as TimelineExportV1;

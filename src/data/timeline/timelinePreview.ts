/**
 * 开发预览数据入口：Cycle-Research 真实导出（timeline_export_v1，canonical Contract）。
 *
 * - JSON 为 exports/timeline_export_v1.json 的逐字节拷贝（Cycle 只消费、不修改；
 *   所有业务结构变更回 Research 项目完成）。
 * - 预览数据不是生产数据出口：不写入 data/verified、不混入 allCampaigns
 *   （由 timelineAdapter 测试断言保证）。
 * - 优先「原始 JSON + Adapter 读取」：静态 import，无运行时网络请求（静态 PWA 不变）。
 */
import timelineExportV1Json from './data/timeline_export_v1.json';
import type { TimelineExportV1 } from './timelineTypes';

/** Cycle-Research 真实导出数据（v1.0；经 timelineAdapter 校验后使用） */
export const timelineExportData = timelineExportV1Json as unknown as TimelineExportV1;

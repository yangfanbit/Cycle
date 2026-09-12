/**
 * 数据层唯一出口（barrel）。
 * 实体数据自 V1.5 起迁移至根目录 data/（raw / candidate / verified / validation 四层，
 * 语义见 data/README.md 与 docs/HISTORICAL_VALIDATION.md），
 * 应用代码只从本文件导入，不直接引用 data/ 内部路径。
 */
import type { Event } from '../models';
import { resolveEventForYear } from '../utils';
import { events } from '../../data/candidate/events';

export * from '../../data/raw/sources';
export * from '../../data/raw/excerpts';
export * from '../../data/candidate/rules';
export * from '../../data/candidate/campaigns';
export * from '../../data/candidate/themes';
export * from '../../data/candidate/events';
export * from '../../data/verified/campaigns';
export * from '../../data/validation/evidence';
export * from '../../data/validation/records';
export * from '../../data/validation/pilot';

/** 锚点事件解析器：供 windowStatus 计算 relative_event 窗口使用 */
export function anchorResolver(eventId: string, seasonYear: number): string | null {
  const event: Event | undefined = events.find((e) => e.event_id === eventId);
  if (!event) return null;
  const resolved = resolveEventForYear(event, seasonYear);
  return resolved ? resolved.start : null;
}

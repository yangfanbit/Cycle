import type { Event } from '../models';
import { resolveEventForYear } from '../utils';
import { events } from './events';

export * from './sources';
export * from './themes';
export * from './events';
export * from './rules';
export * from './campaigns';

/** 锚点事件解析器：供 windowStatus 计算 relative_event 窗口使用 */
export function anchorResolver(eventId: string, seasonYear: number): string | null {
  const event: Event | undefined = events.find((e) => e.event_id === eventId);
  if (!event) return null;
  const resolved = resolveEventForYear(event, seasonYear);
  return resolved ? resolved.start : null;
}

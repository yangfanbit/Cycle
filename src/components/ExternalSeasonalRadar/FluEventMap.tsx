/**
 * 流感事件地图 —— `HistoricalEventMap` 的**薄封装**（保留既有导出名与语义）。
 *
 * ★ 通用化（2026-10-14）后，展示逻辑全部在 `HistoricalEventMap`；
 *   本组件只负责注入**流感题材**的数据与展示配置。
 * ★ 流感专属语义（业务机制 / 负面参照 / 证据边界 / 邻近事件免责声明）由
 *   `flu_historical_events_v0_4.json` + 索引的 `display` 提供，**未丢失**。
 */
import { HistoricalEventMap } from './HistoricalEventMap';
import { fluEventsDoc } from '../../data/timeline/fluHistoricalEvents';
import {
  eventMapByTheme,
  type HistoricalEventsDoc,
} from '../../data/timeline/historicalEventMaps';

export function FluEventMap() {
  const doc = fluEventsDoc() as unknown as HistoricalEventsDoc;
  const entry = eventMapByTheme('FLU');
  return <HistoricalEventMap doc={doc} display={entry?.display} />;
}

import type {
  LifecycleEntry,
  LifecycleTimeline,
  MarketSnapshot,
  SnapshotObservation,
} from './types';

/**
 * Lifecycle Tracking —— 当前对象的**追加式观察时间线**（ThreeC 1.1 Phase 1.4）。
 *
 * ## 设计要点（见 `docs/THREEC_1_1_LIFECYCLE_TRACKING_DESIGN.md`）
 * 1. **派生，不新增 artifact** —— 时间线**从快照序列派生**（按 `linked_object_id` 分组）。
 *    单一事实来源；append-only 由构造保证；不可能与快照不一致。
 * 2. **禁 look-ahead（PIT 安全）** —— 必须传 `asOf`：**只回放该日期之前的快照**。
 *    否则会用「10 月才登记的信息」去解释「9 月的状态」，这正是 look-ahead。
 * 3. **只陈述事实** —— 不做阶段判断、不做因果推断、不给评分。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络、无随机。相同输入必得相同输出。
 */

/** 该观察是否属于某对象 */
function belongsTo(o: SnapshotObservation, objectId: string): boolean {
  return (o.linked_object_id ?? null) === objectId;
}

function toEntry(o: SnapshotObservation, firstSeenIn: string): LifecycleEntry {
  return {
    date: o.date,
    observation_id: o.observation_id,
    observation_type: o.observation_type,
    claim: o.claim,
    evidence_strength: o.evidence_strength,
    direction: o.direction,
    source_tier: o.source_tier,
    source_title: o.source_title,
    first_seen_in: firstSeenIn,
  };
}

/**
 * 派生某对象的观察时间线。
 *
 * @param snapshots 快照序列（**任意顺序**，内部按 `snapshot_date` 升序处理）
 * @param objectId  当前研究对象 id
 * @param asOf      ★ PIT 上界（含）：只使用 `snapshot_date <= asOf` 的快照。
 *                  **强烈建议始终传入** —— 不传就等于「用全部历史去看过去」，存在 look-ahead 风险。
 */
export function lifecycleTimelineOf(
  snapshots: MarketSnapshot[],
  objectId: string,
  asOf?: string,
): LifecycleTimeline {
  const ordered = [...snapshots]
    .filter((s) => (asOf ? s.snapshot_date <= asOf : true))
    .sort((a, b) => `${a.snapshot_date}::${a.snapshot_id}`.localeCompare(`${b.snapshot_date}::${b.snapshot_id}`));

  const seen = new Map<string, LifecycleEntry>();
  let displayName = objectId;

  for (const snap of ordered) {
    for (const obj of snap.research_objects ?? []) {
      if (obj.object_id === objectId) displayName = obj.display_name;
    }
    for (const o of snap.observations ?? []) {
      if (!belongsTo(o, objectId)) continue;
      // ★ append-only：同一 observation_id 只取**最早**登记的那一期，后续期不得覆盖
      if (seen.has(o.observation_id)) continue;
      seen.set(o.observation_id, toEntry(o, snap.snapshot_id));
    }
  }

  const entries = [...seen.values()].sort((a, b) =>
    `${a.date}::${a.observation_id}`.localeCompare(`${b.date}::${b.observation_id}`),
  );

  return {
    object_id: objectId,
    display_name: displayName,
    entries,
    count: entries.length,
    first_date: entries.length ? entries[0].date : null,
    last_date: entries.length ? entries[entries.length - 1].date : null,
  };
}

/** 快照里出现过的全部当前对象 id（按 id 升序，稳定顺序） */
export function trackedObjectIds(snapshots: MarketSnapshot[], asOf?: string): string[] {
  const ids = new Set<string>();
  for (const s of snapshots) {
    if (asOf && s.snapshot_date > asOf) continue;
    for (const o of s.research_objects ?? []) ids.add(o.object_id);
  }
  return [...ids].sort();
}

/** 一次性派生全部对象的时间线 */
export function lifecycleTimelinesOf(
  snapshots: MarketSnapshot[],
  asOf?: string,
): LifecycleTimeline[] {
  return trackedObjectIds(snapshots, asOf).map((id) => lifecycleTimelineOf(snapshots, id, asOf));
}

/**
 * ★ append-only 自检：同一 `observation_id` 在不同快照里**内容必须一致**。
 * 返回不一致的条目（空数组 = 通过）。校验器 **L3** 用同一逻辑。
 */
export function findRewrittenObservations(
  snapshots: MarketSnapshot[],
): { observation_id: string; snapshots: string[]; fields: string[] }[] {
  const first = new Map<string, { snap: string; o: SnapshotObservation }>();
  const bad = new Map<string, { snapshots: Set<string>; fields: Set<string> }>();

  const ordered = [...snapshots].sort((a, b) =>
    `${a.snapshot_date}::${a.snapshot_id}`.localeCompare(`${b.snapshot_date}::${b.snapshot_id}`),
  );

  for (const snap of ordered) {
    for (const o of snap.observations ?? []) {
      const prev = first.get(o.observation_id);
      if (!prev) {
        first.set(o.observation_id, { snap: snap.snapshot_id, o });
        continue;
      }
      const diff = (['date', 'claim', 'observation_type', 'evidence_strength', 'direction'] as const)
        .filter((k) => (prev.o[k] ?? null) !== (o[k] ?? null));
      if (diff.length > 0) {
        const cur = bad.get(o.observation_id) ?? { snapshots: new Set([prev.snap]), fields: new Set<string>() };
        cur.snapshots.add(snap.snapshot_id);
        diff.forEach((d) => cur.fields.add(d));
        bad.set(o.observation_id, cur);
      }
    }
  }

  return [...bad.entries()].map(([observation_id, v]) => ({
    observation_id,
    snapshots: [...v.snapshots].sort(),
    fields: [...v.fields].sort(),
  }));
}

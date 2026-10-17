/**
 * 剪贴板复制（ThreeC 1.3 · v0.8）—— **可测**、**分级降级**、**绝不假报成功**。
 *
 * ## 为什么单独成模块
 * v0.7 的 `copy()` 失败时只做 `setCopied(null)`：既**不告诉用户失败了**，
 * 也不给下一步（导出预览还是折叠的 `<details>`）。用户点「复制 JSON」后毫无反馈，
 * 只能猜「到底复制上没」。
 *
 * ## 现实约束（均已实测）
 * - `navigator.clipboard` 是 **Secure Context 限定**：`https:` 可用；本地 `vite preview` 的
 *   http LAN 地址、部分旧浏览器**不可用**（`window.isSecureContext === false` 时不存在）。
 * - 权限被拒绝（`NotAllowedError`）与**根本没有 API** 是两回事，必须**分开报告**。
 * - 降级用的 `document.execCommand('copy')` 在现代浏览器仍实现，但：
 *   ★ **jsdom 未实现**（实测 `typeof document.execCommand === 'undefined'`）——
 *     所以这条分支在测试里只能显式 stub 才能覆盖（不假装测过了）。
 *
 * ★ 依赖通过参数注入，模块本身**无 IO** → 可在 node 下直测。
 */

/** 复制结果：要么成功（说明用了哪条路径），要么失败（说明为什么） */
export type CopyOutcome =
  | { ok: true; via: 'clipboard' | 'execCommand' }
  | { ok: false; reason: 'unavailable' | 'rejected' | 'no_dom' | 'no_platform' | 'unknown'; detail: string };

/** 注入的运行环境（测试传桩实现；生产传真实 DOM） */
export interface ClipboardEnv {
  /** `navigator.clipboard`（不存在 → null） */
  clipboard: { writeText(text: string): Promise<void> } | null;
  /** `document.execCommand`（jsdom 下不存在 → undefined） */
  execCommand?: (command: string) => boolean;
  /** 是否在 DOM 环境里（node 测试里为 false） */
  hasDom: boolean;
}

/** 从**当前全局**取运行环境（唯一触碰 DOM 的地方） */
export function currentClipboardEnv(): ClipboardEnv {
  const nav = typeof navigator === 'undefined' ? undefined : navigator;
  const hasDom = typeof document !== 'undefined';
  return {
    clipboard: nav && 'clipboard' in nav ? (nav.clipboard as ClipboardEnv['clipboard']) : null,
    execCommand: hasDom ? (cmd: string) => (document as unknown as { execCommand?: (c: string) => boolean }).execCommand?.(cmd) ?? false : undefined,
    hasDom,
  };
}

/** 把复制失败翻成**给用户看的一句话**（含下一步该做什么） */
export function copyFailureMessage(o: CopyOutcome & { ok: false }): string {
  switch (o.reason) {
    case 'unavailable':
      return '复制失败：当前浏览器或上下文不提供剪贴板能力（非 HTTPS / 旧浏览器 / 权限被禁用）。';
    case 'rejected':
      return `复制失败：剪贴板权限被拒绝（${o.detail}）。`;
    case 'no_dom':
      return '复制失败：当前不是浏览器环境，无法访问剪贴板。';
    case 'no_platform':
      return '复制失败：没有可用的复制途径。';
    default:
      return `复制失败：${o.detail || '未知原因'}。`;
  }
}

/** 成功时的一句话（**只有真的成功才出现**） */
export function copySuccessMessage(o: CopyOutcome & { ok: true }): string {
  return o.via === 'clipboard' ? '已复制到剪贴板 ✓' : '已复制（兼容模式）✓';
}

/**
 * 尝试复制；按 `navigator.clipboard` → `execCommand` 顺序降级。
 * **任何情况都不抛错** —— 失败转结果对象，由调用方告知用户并展开备用导出。
 */
export async function copyTextToClipboard(
  text: string,
  env: ClipboardEnv = currentClipboardEnv(),
): Promise<CopyOutcome> {
  if (!env.hasDom) return { ok: false, reason: 'no_dom', detail: 'no document' };

  if (env.clipboard) {
    try {
      await env.clipboard.writeText(text);
      return { ok: true, via: 'clipboard' };
    } catch (e) {
      // 有些浏览器在不可用时**同步抛**（访问 .writeText 即 TypeError），一并接住
      const name = e instanceof Error ? e.name : '';
      const detail = e instanceof Error ? e.message : String(e);
      if (name === 'NotAllowedError' || name === 'SecurityError' || name === 'PermissionDeniedError') {
        return { ok: false, reason: 'rejected', detail };
      }
      // 其它错误：继续尝试 execCommand 降级
    }
  }

  if (env.execCommand) {
    try {
      const ok = env.execCommand('copy');
      return ok
        ? { ok: true, via: 'execCommand' }
        : { ok: false, reason: 'no_platform', detail: 'execCommand returned false' };
    } catch (e) {
      return {
        ok: false,
        reason: 'unknown',
        detail: e instanceof Error ? e.message : String(e),
      };
    }
  }

  return {
    ok: false,
    reason: env.clipboard ? 'no_platform' : 'unavailable',
    detail: env.clipboard ? 'clipboard 失败且无 execCommand 降级' : 'navigator.clipboard 不存在',
  };
}

import { describe, it, expect } from 'vitest';

import {
  copyFailureMessage,
  copySuccessMessage,
  copyTextToClipboard,
  currentClipboardEnv,
  type ClipboardEnv,
} from '../clipboard';

/**
 * 剪贴板复用的降级与语义（v0.8）。
 *
 * ★ 为什么用**注入 env**：`document.execCommand` 在 jsdom **未实现**
 * （实测 `typeof document.execCommand === 'undefined'`），jsdom 的
 * `getSelection().toString()` 也恒为 `''` —— 无法忠实模拟「有选区」前提。
 * → 降级路径在这里以**注入 ClipboardEnv** 覆盖，交互层（draftInteraction.test.tsx）
 * 则覆盖「无 clipboard → 失败提示 + 展开预览」。**不假装跨两端都测过同一件事**。
 */

const okWriter = (calls: string[]) => async () => { calls.push('x'); };

describe('copyTextToClipboard 降级链', () => {
  it('① 有 navigator.clipboard 且成功 → via clipboard', async () => {
    const env: ClipboardEnv = { hasDom: true, clipboard: { writeText: okWriter(['a']) } };
    expect(await copyTextToClipboard('t', env)).toEqual({ ok: true, via: 'clipboard' });
  });

  it('② clipboard 抛权限错误 → rejected（**不**继续尝试 execCommand，因为明确被拒）', async () => {
    const env: ClipboardEnv = {
      hasDom: true,
      clipboard: {
        writeText: () => { const e = new Error('nope'); e.name = 'NotAllowedError'; throw e; },
      },
      execCommand: () => true,
    };
    const r = await copyTextToClipboard('t', env);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('rejected');
  });

  it('③ clipboard 同步抛 TypeError（部分浏览器访问 .writeText 即抛）→ 落到 execCommand', async () => {
    const env: ClipboardEnv = {
      hasDom: true,
      clipboard: {
        writeText: () => { throw new TypeError('Cannot read properties of undefined'); },
      },
      execCommand: () => true,
    };
    expect(await copyTextToClipboard('t', env)).toEqual({ ok: true, via: 'execCommand' });
  });

  it('④ **完全没有** navigator.clipboard → 走 execCommand 降级', async () => {
    const env: ClipboardEnv = { hasDom: true, clipboard: null, execCommand: () => true };
    expect(await copyTextToClipboard('t', env)).toEqual({ ok: true, via: 'execCommand' });
  });

  it('⑤ clipboard 与 execCommand 都不可用 → unavailable', async () => {
    const env: ClipboardEnv = { hasDom: true, clipboard: null, execCommand: undefined };
    const r = await copyTextToClipboard('t', env);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('unavailable');
  });

  it('⑥ clipboard 失败 + execCommand 返回 false → no_platform', async () => {
    const env: ClipboardEnv = {
      hasDom: true,
      clipboard: { writeText: () => { throw new Error('boom'); } },
      execCommand: () => false,
    };
    const r = await copyTextToClipboard('t', env);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('no_platform');
  });

  it('⑦ 非 DOM 环境 → no_dom（node 下直测）', async () => {
    const r = await copyTextToClipboard('t', { hasDom: false, clipboard: null });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toBe('no_dom');
  });

  it('★ 任何路径都不抛错', async () => {
    const envs: ClipboardEnv[] = [
      { hasDom: false, clipboard: null },
      { hasDom: true, clipboard: null },
      { hasDom: true, clipboard: { writeText: () => Promise.reject(new Error('x')) } },
      { hasDom: true, clipboard: null, execCommand: () => { throw new Error('y'); } },
    ];
    for (const e of envs) {
      await expect(copyTextToClipboard('t', e)).resolves.toBeTruthy();
    }
  });
});

describe('给用户的文案', () => {
  it('★ 只有在成功时才会出现「已复制」', () => {
    expect(copySuccessMessage({ ok: true, via: 'clipboard' })).toContain('已复制');
    expect(copySuccessMessage({ ok: true, via: 'execCommand' })).toContain('已复制');
    // 失败文案里**不许**出现「已复制」
    for (const m of [
      copyFailureMessage({ ok: false, reason: 'unavailable', detail: '' }),
      copyFailureMessage({ ok: false, reason: 'rejected', detail: 'NotAllowedError' }),
      copyFailureMessage({ ok: false, reason: 'no_dom', detail: '' }),
      copyFailureMessage({ ok: false, reason: 'no_platform', detail: '' }),
    ]) {
      expect(m).toContain('复制失败');
      expect(m).not.toContain('已复制');
    }
  });

  it('★ 失败文案说明原因', () => {
    expect(copyFailureMessage({ ok: false, reason: 'rejected', detail: 'NotAllowedError' }))
      .toContain('权限被拒绝');
    expect(copyFailureMessage({ ok: false, reason: 'unavailable', detail: '' }))
      .toContain('非 HTTPS');
  });
});

describe('currentClipboardEnv（node 环境）', () => {
  it('★ node 下安全返回（不抛错），hasDom=false', () => {
    const env = currentClipboardEnv();
    expect(env.hasDom).toBe(false);
    expect(env.clipboard).toBeNull();
  });
});

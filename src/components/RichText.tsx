/**
 * ★★ 源数据文本里的 `**强调**` → `<strong>`。
 *
 * 研究侧写的 Markdown（`display.note` / `outcome_rule` / `rationale` …）如果直接塞进 JSX，
 * 会**原样显示两个星号**（本项目已知陷阱）。所有渲染研究侧字符串的地方都走这里。
 *
 * - 可见文本用 `<RichText />`；
 * - 属性（`title` 等）不能放标签，用 `plain()` 去掉标记。
 */
export function RichText({ text }: { text: string }) {
  const parts = text.split('**');
  return (
    <>
      {parts.map((p, i) => (i % 2 === 1 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>))}
    </>
  );
}

/** 纯文本化：把 `**` 去掉（用于 `title` 等属性） */
export function plain(text: string): string {
  return text.split('**').join('');
}

// formula — a formula or a chain of cause and effect in one row of large words with operators between.
// The row is sized to fit: 1500 / (characters + 1.2 per operator), CJK 1, others 0.55,
// at most 190 px (doc_code.formula_params stops below 72: 公式太長).
// p.terms [{text, sub, at, hot}] (2-5; sub: one small line under the term; hot: lands with slamIn, keep for the 3-5
//   numbers a film turns on) · p.ops [..] (one fewer than terms: = + − × ÷ → > <; each comes in with the term on its
//   right) · p.focus [{i, at}] (frame around term i, the other terms dim to .25) · p.strike [{i, at}] (red line through
//   term i) · p.title (card top-left) · p.note (small caption bottom-right)
SCENES.formula = p => {
  const terms = p.terms, ops = p.ops || [], y = 410, MUTED = cv("--muted") || FG;
  const cjk = /[⺀-鿿가-힯豈-﫿＀-￯]/;
  const units = terms.reduce((a, t) => a + [...String(t.text)].reduce((s, c) => s + (cjk.test(c) ? 1 : .55), 0), 0) + 1.2 * ops.length;
  const size = Math.min(190, Math.floor(1500 / units)), gap = size * .3;
  if (p.title) popIn(box(p.title, { x: 90, y: 70, cls: "card", size: 52, rot: -1 }), at(p.title_at, .1));
  const big = b => (Object.assign(b.style, { fontFamily: "var(--font-big)", fontWeight: 900, lineHeight: 1, whiteSpace: "nowrap" }), b);
  const T = terms.map(t => big(box(`<span${t.hot ? ' class="hot"' : ""}>${t.text}</span>`, { x: 0, y, size, cls: "term" })));
  const O = ops.map(o => { const b = box(o, { x: 0, y, size, cls: "op" }); big(b); b.style.fontWeight = 700; return b; });
  // lay the row out: term, op, term ... centred on 960 (the template builds scenes once the fonts are in, so the widths are
  // the real font's); everything hung on a term (sub, frame, strike) is its child and follows.
  const row = T.flatMap((b, k) => k ? [O[k - 1], b] : [b]);
  const layout = () => {
    let x = 960 - (row.reduce((a, b) => a + b.offsetWidth, 0) + gap * (row.length - 1)) / 2;
    row.forEach(b => { b.style.left = x + "px"; x += b.offsetWidth + gap; });
  };
  layout();
  const hang = (b, cls, css) => { const d = document.createElement("div"); d.className = cls; b.appendChild(d);
    Object.assign(d.style, { position: "absolute" }, css); return d; };
  const S = terms.map((t, k) => {
    const tt = at(t.at, .4 + k * .7);
    if (t.hot) slamIn(T[k], tt); else { popIn(T[k], tt); sfx("pop", tt); }
    if (k) popIn(O[k - 1], tt);
    if (!t.sub) return null;
    const s = hang(T[k], "sub", { left: "50%", top: "calc(100% + 18px)", transform: "translateX(-50%)", whiteSpace: "nowrap",
      fontFamily: "var(--font-ui)", fontWeight: 700, fontSize: "44px", lineHeight: 1.2, color: MUTED, opacity: 0 });
    s.innerHTML = `<span>${t.sub}</span>`;
    tl.to(s, { opacity: 1, duration: .3 }, tt + .2); return s.firstChild;
  });
  const spans = T.map(b => b.firstChild), frames = [];
  (p.focus || []).forEach(f => {
    const t = at(f.at, D - TAIL - 1.5);
    const fr = hang(T[f.i], "frame", { left: "-18px", right: "-18px", top: "-14px", bottom: "-14px", border: `5px solid ${RED}`,
      borderRadius: "16px", opacity: 0 });
    frames.forEach(o => tl.to(o, { opacity: 0, duration: .3 }, t));
    tl.to(fr, { opacity: 1, duration: .3 }, t); frames.push(fr);
    focusDim(spans, f.i, t); focusDim(S, f.i, t); sfx("marker", t);
  });
  (p.strike || []).forEach(s => {
    const t = at(s.at, D - TAIL - 1.5);
    const u = hang(T[s.i], "strike", { left: 0, top: "calc(50% - 4px)", width: "0%", height: "8px", background: RED, borderRadius: "4px" });
    u.dataset.i = s.i;
    tl.to(u, { width: "100%", duration: .35, ease: TORN ? "steps(4)" : "power2.out" }, t);
  });
  if (p.note) { const c = box(p.note, { x: 0, y: 824, size: 32 }); c.style.left = (1830 - c.offsetWidth) + "px"; c.style.opacity = 0;
    tl.to(c, { opacity: .7, duration: .5 }, at(p.note_at, .8)); }
};

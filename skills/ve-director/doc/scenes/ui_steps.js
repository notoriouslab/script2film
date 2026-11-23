// ui_steps — a drawn, simplified app panel whose parts change state on the spoken word (click, switch, tick, type, send).
// For "how to use an app" beats with nothing worth recording (or a screen that would show an account). Parts are drawn in
// the theme's colours and never copy a real app's look.
// p.title · p.cursor (default true) · p.widgets: 1-5 of
//   {kind: "card", text, sub, icon}            icon: app / folder / code / film / check (default app)
//   {kind: "button", text, press_at}
//   {kind: "toggle", options: [2-3], picks: [{pick, at}]}
//   {kind: "menu", label, items: [2-5], pick, pick_at, open_at}
//   {kind: "check", text, check_at}
//   {kind: "input", text, type_at, send_at}
//   {kind: "chips", items: [{text, at, off}]}       off: struck through, "not needed"
// every part may carry "at" (when it appears). Timing rules (set on a moving preview, 2026-11-23): a part without "at"
// appears 0.5 s before its first action at the latest; no action lands earlier than 0.35 s after its part appears (a line
// that opens on the action lags the voice by that much instead of clicking an empty panel); a menu picks 0.35 s after it
// opens; an input sends 0.2 s after it finishes typing. The panel sits centred in the 150-860 band and a short panel grows
// up to 1.35x (p._scale_max: doc_code sets 1.0 on a beat with an avatar peek, which would sit on an enlarged panel).
// The page exposes window.__ui (each part's box) and window.__uit (each action's second) for the tests.
SCENES.ui_steps = p => {
  if (!document.getElementById("uicss")) { const st = document.createElement("style"); st.id = "uicss"; st.textContent = `
    .uis-panel{position:absolute;left:410px;width:1100px;top:150px;border-radius:22px;padding:36px 50px;box-sizing:border-box;z-index:22;
      background:var(--uis-panel);box-shadow:0 18px 50px rgba(0,0,0,.35),inset 0 0 0 2px var(--uis-line);font-family:var(--font-ui);color:var(--fg)}
    .uis-title{font-size:46px;font-weight:800;color:var(--red);height:62px;margin-bottom:28px;white-space:nowrap}
    .uis-w{position:relative;margin-bottom:28px;transform-origin:20% 50%}
    .uis-w:last-child{margin-bottom:0}
    .uis-w.menu{z-index:5}
    .uis-row{display:flex;align-items:center;gap:22px;height:96px;border-radius:16px;background:var(--uis-well);
      box-shadow:inset 0 0 0 2px var(--uis-line);padding:0 28px;box-sizing:border-box;font-size:40px;overflow:hidden}
    .uis-icon{width:72px;height:72px;border-radius:16px;background:var(--red);color:var(--uis-on);display:grid;place-items:center;font-size:38px;font-weight:800;flex:none}
    .uis-sub{font-size:28px;color:var(--uis-muted)}
    .uis-btn{display:inline-flex;align-items:center;justify-content:center;height:96px;padding:0 48px;border-radius:48px;box-sizing:border-box;
      box-shadow:inset 0 0 0 3px var(--red);color:var(--red);font-size:40px;font-weight:700;white-space:nowrap}
    .uis-track{position:relative;display:flex;height:96px;border-radius:48px;background:var(--uis-well);box-shadow:inset 0 0 0 2px var(--uis-line);width:640px}
    .uis-opt{flex:1;display:grid;place-items:center;font-size:38px;font-weight:700;position:relative;z-index:2}
    .uis-thumb{position:absolute;top:8px;bottom:8px;left:8px;border-radius:40px;z-index:1}
    .uis-list{position:absolute;left:0;top:104px;width:520px;border-radius:16px;background:var(--bg-solid);padding:10px;box-sizing:border-box;
      box-shadow:0 14px 30px rgba(0,0,0,.45),inset 0 0 0 2px var(--uis-line);transform-origin:20% 0;opacity:0}
    .uis-item{height:72px;display:flex;align-items:center;padding:0 22px;border-radius:12px;font-size:36px}
    .uis-box{width:56px;height:56px;border-radius:12px;box-shadow:inset 0 0 0 3px var(--uis-muted);flex:none;position:relative}
    .uis-input{height:140px;align-items:flex-start;padding-top:16px;padding-bottom:16px}
    .uis-txt{flex:1;font-family:ui-monospace,Menlo,monospace;font-size:28px;line-height:1.3;height:108px;overflow:hidden;word-break:break-word}
    .uis-ph{position:absolute;left:28px;top:16px;font-family:ui-monospace,Menlo,monospace;font-size:28px;line-height:1.3;color:var(--uis-muted)}
    .uis-send{width:76px;height:76px;border-radius:50%;flex:none;display:grid;place-items:center;font-size:40px;font-weight:800;align-self:center;
      background:var(--uis-well);box-shadow:inset 0 0 0 2px var(--uis-line)}
    .uis-chips{display:flex;gap:18px;height:80px;align-items:center;overflow:hidden}
    .uis-chip{padding:12px 28px;border-radius:40px;font-size:34px;box-shadow:inset 0 0 0 2px var(--uis-muted);white-space:nowrap;opacity:0}
    .uis-cursor{position:absolute;left:0;top:0;width:44px;height:44px;z-index:30;opacity:0}`;
    document.head.appendChild(st); }
  const root = document.getElementById("root"), ACC = cv("--red"), ON = BG;
  const clear = v => !v || /rgba\(0,\s*0,\s*0,\s*0\)|transparent/.test(v);
  root.style.setProperty("--uis-panel", clear(cv("--strip")) ? "rgba(255,255,255,.06)" : cv("--strip"));   // live: --strip is transparent
  root.style.setProperty("--uis-well", `color-mix(in srgb, ${BG} 70%, transparent)`);
  root.style.setProperty("--uis-line", `color-mix(in srgb, ${FG} 22%, transparent)`);
  root.style.setProperty("--uis-muted", cv("--muted") || `color-mix(in srgb, ${FG} 60%, transparent)`);
  root.style.setProperty("--uis-on", ON);
  const panel = document.createElement("div"); panel.className = "uis-panel"; CONTENT.appendChild(panel);
  if (p.title) { const h = document.createElement("div"); h.className = "uis-title"; h.textContent = p.title; panel.appendChild(h); }
  const W = p.widgets || [], acts = [];
  const lead = w => [w.press_at, w.pick_at, w.open_at, w.check_at, w.type_at, ...(w.picks || []).map(x => x.at),
                     ...(w.kind === "chips" ? w.items.map(x => x.at) : [])].filter(v => v != null).map(v => at(v, null)).filter(Number.isFinite);
  const parts = W.map((w, k) => {
    const d = document.createElement("div"); d.className = "uis-w " + w.kind; panel.appendChild(d);
    let show = w.at != null ? at(w.at, .3 + k * .6) : .3 + k * .6;
    const first = lead(w); if (w.at == null && first.length) show = Math.max(0, Math.min(show, Math.min(...first) - .5));
    const A = (v, f) => Math.max(at(v, f), show + .35);
    const o = { w, d, show };
    if (w.kind === "card") {
      const ic = { app: "▶", folder: "▤", code: "{ }", film: "▣", check: "✓" }[w.icon || "app"] || "▶";
      d.innerHTML = `<div class="uis-row" style="height:120px"><div class="uis-icon">${ic}</div><div>${w.text}${w.sub ? `<div class="uis-sub">${w.sub}</div>` : ""}</div></div>`;
    } else if (w.kind === "button") {
      d.innerHTML = `<div class="uis-btn">${w.text}</div>`; o.btn = d.firstChild;
      if (w.press_at != null) { o.press = A(w.press_at, show + .6); acts.push({ t: o.press, el: o.btn }); }
    } else if (w.kind === "toggle") {
      d.innerHTML = `<div class="uis-track"><div class="uis-thumb"></div>${w.options.map(x => `<div class="uis-opt">${x}</div>`).join("")}</div>`;
      o.thumb = d.querySelector(".uis-thumb"); o.opts = [...d.querySelectorAll(".uis-opt")];
      let last = show; o.picks = w.picks.map(x => { const t = Math.max(A(x.at, last + .6), last); last = t + .35; return { i: w.options.indexOf(x.pick), t }; });
      o.picks.forEach(x => acts.push({ t: x.t, el: o.opts[x.i] }));
    } else if (w.kind === "menu") {
      d.innerHTML = `<div class="uis-row" style="width:520px"><span class="lab" style="position:relative"><span class="a">${w.label}</span>`
        + `<span class="b" style="position:absolute;left:0;opacity:0">${w.pick}</span></span><span style="margin-left:auto;color:var(--uis-muted)">▾</span></div>`
        + `<div class="uis-list">${w.items.map(x => `<div class="uis-item">${x}</div>`).join("")}</div>`;
      o.row = d.firstChild; o.list = d.querySelector(".uis-list"); o.items = [...d.querySelectorAll(".uis-item")];
      const pk = at(w.pick_at, show + 1);
      o.open = A(w.open_at != null ? w.open_at : pk - .6, pk - .6); o.pick = Math.max(pk, o.open + .35); o.pi = w.items.indexOf(w.pick);
      acts.push({ t: o.open, el: o.row }, { t: o.pick, el: o.items[o.pi] });
    } else if (w.kind === "check") {
      d.innerHTML = `<div class="uis-row" style="height:88px"><div class="uis-box"><svg viewBox="0 0 56 56" width="56" height="56" style="position:absolute;inset:0">`
        + `<path d="M14 29 L24 39 L43 18" fill="none" stroke="${ACC}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="44" stroke-dashoffset="44"/></svg></div><span>${w.text}</span></div>`;
      o.row = d.firstChild; o.box = d.querySelector(".uis-box"); o.path = d.querySelector("path");
      o.check = A(w.check_at, show + .6); acts.push({ t: o.check, el: o.box });
    } else if (w.kind === "input") {
      d.innerHTML = `<div class="uis-row uis-input" style="position:relative"><div class="uis-txt"></div><div class="uis-ph"></div><div class="uis-send">↑</div></div>`;
      o.txt = d.querySelector(".uis-txt"); o.send = d.querySelector(".uis-send");
      o.type = A(w.type_at, show + .4); const s = at(w.send_at, o.type + 2.6);
      o.dur = Math.max(.6, Math.min(w.text.length * .03, 2.2, s - o.type - .2)); o.sent = Math.max(s, o.type + o.dur + .2);
      acts.push({ t: o.sent, el: o.send });
    } else if (w.kind === "chips") {
      d.innerHTML = `<div class="uis-chips">${w.items.map(x => `<span class="uis-chip">${x.text}</span>`).join("")}</div>`;
      o.chips = [...d.querySelectorAll(".uis-chip")].map((c, i) => ({ c, t: Math.max(at(w.items[i].at, show + .3 + i * .5), show), off: w.items[i].off }));
    }
    return o;
  });
  // size and place: centred in the 150-860 band, a short panel enlarged (the scale is measured on the real fonts)
  const h0 = panel.offsetHeight, sc = Math.min(p._scale_max ?? 1.35, 710 / h0), top = 505 - h0 * sc / 2;
  panel.style.top = top + "px"; gsap.set(panel, { scale: sc, transformOrigin: "50% 0", opacity: 0, y: 24 });
  tl.to(panel, { opacity: 1, y: 0, duration: .4, ease: "power2.out" }, 0);
  const R = root.getBoundingClientRect(), box = e => { const r = e.getBoundingClientRect();
    return { left: r.left - R.left, top: r.top - R.top, right: r.right - R.left, bottom: r.bottom - R.top, cx: r.left - R.left + r.width * .45, cy: r.top - R.top + r.height / 2 }; };
  gsap.set(panel, { y: 0 }); const where = acts.map(a => ({ t: a.t, ...box(a.el) }));   // measured at rest, then put back
  window.__ui = parts.map(o => ({ kind: o.w.kind, show: o.show, ...box(o.d) }));
  gsap.set(panel, { y: 24 });
  const T2 = []; const mark = (kind, t, what) => { sfx(kind, t); T2.push({ what, t: Math.round(t * 1000) / 1000 }); };
  parts.forEach((o, k) => {
    const w = o.w;
    gsap.set(o.d, { opacity: 0, scale: .92 });
    tl.to(o.d, { opacity: 1, scale: 1, duration: .35, ease: "back.out(1.6)" }, o.show);
    if (w.kind === "card") mark("pop", o.show, `${k}:show`);
    if (w.kind === "button" && o.press != null) {
      tl.to(o.btn, { scale: .94, duration: .09, ease: "power1.out" }, o.press);
      tl.to(o.btn, { scale: 1, duration: .18, ease: "back.out(2)" }, o.press + .09);
      tl.set(o.btn, { backgroundColor: ACC, color: ON }, o.press); mark("click", o.press, `${k}:press`);
    }
    if (w.kind === "toggle") {
      const seg = 640 / w.options.length;
      gsap.set(o.thumb, { width: seg - 16, backgroundColor: `color-mix(in srgb, ${FG} 22%, transparent)` });
      let from = 0;
      o.picks.forEach((x, j) => {
        if (x.i !== from) tl.to(o.thumb, { x: x.i * seg, duration: .35, ease: "power2.inOut" }, x.t);
        if (j === 0) tl.set(o.thumb, { backgroundColor: ACC }, x.t);
        o.opts.forEach((e, i) => tl.set(e, { color: i === x.i ? ON : FG }, x.t + (x.i !== from ? .18 : 0)));
        mark("click", x.t, `${k}:pick${j}`); from = x.i;
      });
    }
    if (w.kind === "menu") {
      gsap.set(o.list, { opacity: 0, scaleY: .85 });
      tl.to(o.list, { opacity: 1, scaleY: 1, duration: .25, ease: "power2.out" }, o.open); mark("click", o.open, `${k}:open`);
      tl.set(o.items[o.pi], { backgroundColor: ACC, color: ON }, o.pick); mark("tick", o.pick, `${k}:pick`);
      tl.to(o.list, { opacity: 0, duration: .2 }, o.pick + .3);
      tl.set(o.d.querySelector(".a"), { opacity: 0 }, o.pick + .3); tl.set(o.d.querySelector(".b"), { opacity: 1 }, o.pick + .3);
      tl.set(o.row, { boxShadow: `inset 0 0 0 3px ${ACC}` }, o.pick + .3);
    }
    if (w.kind === "check") {
      tl.to(o.path, { strokeDashoffset: 0, duration: .3, ease: "power2.out" }, o.check);
      tl.set([o.box, o.row], { boxShadow: `inset 0 0 0 3px ${ACC}` }, o.check); mark("tick", o.check, `${k}:check`);
    }
    if (w.kind === "input") {
      const n = { v: 0 }, put = () => { o.txt.textContent = w.text.slice(0, Math.round(n.v)); };
      const ph = o.d.querySelector(".uis-ph"); ph.textContent = LANG === "zh" ? "輸入訊息…" : "Type a request…";   // its own layer: the typing tween owns .uis-txt
      tl.set(ph, { opacity: 0 }, o.type);
      tl.fromTo(n, { v: 0 }, { v: w.text.length, duration: o.dur, ease: "none", onUpdate: put, immediateRender: false }, o.type);
      mark("typing", o.type, `${k}:type`);
      tl.set(o.send, { backgroundColor: ACC, color: ON }, o.sent);
      tl.to(o.send, { scale: 1.18, duration: .12, ease: "power1.out", yoyo: true, repeat: 1 }, o.sent);
      tl.to(o.txt, { opacity: .55, duration: .3 }, o.sent + .4); mark("pop", o.sent, `${k}:send`);
    }
    if (w.kind === "chips") o.chips.forEach((c, i) => {
      gsap.set(c.c, { scale: .7 });
      if (c.off) gsap.set(c.c, { textDecoration: "line-through", color: cv("--muted") || FG });
      tl.to(c.c, { opacity: 1, scale: 1, duration: .35, ease: "back.out(1.8)" }, c.t); mark("pop", c.t, `${k}:chip${i}`);
    });
  });
  window.__uit = T2;
  // cursor: glides into each action (start = max(previous action, panel in at 0.4 s, action - 0.45)), presses on it
  if (p.cursor !== false && where.length) {
    const cur = document.createElementNS(NS, "svg"); cur.setAttribute("viewBox", "0 0 44 44"); cur.classList.add("uis-cursor");
    cur.innerHTML = `<path d="M6 4 L6 36 L15 28 L21 41 L27 38 L21 25 L33 25 Z" fill="#fff" stroke="${BG}" stroke-width="2.5" stroke-linejoin="round"/>`;
    CONTENT.appendChild(cur);
    where.sort((a, b) => a.t - b.t);
    gsap.set(cur, { x: where[0].cx - 6, y: where[0].cy - 4, transformOrigin: "6px 4px" });
    let prev = null;
    where.forEach((a, i) => {
      const st = Math.max(a.t - .45, .4, prev ? prev.t : 0);
      if (!prev || a.t - st < .15) { tl.set(cur, { x: a.cx - 6, y: a.cy - 4 }, Math.max(0, st - .01)); if (!prev) tl.to(cur, { opacity: 1, duration: .2 }, Math.max(0, st - .2)); }
      else tl.to(cur, { x: a.cx - 6, y: a.cy - 4, duration: a.t - st, ease: "power2.inOut" }, st);
      tl.to(cur, { scale: .85, duration: .08, yoyo: true, repeat: 1 }, a.t);
      prev = a;
    });
  }
};

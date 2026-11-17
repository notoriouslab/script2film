// timeline — a horizontal line with dated markers appearing as each date is mentioned.
// p.items: [{date: "1950", text: "...", at: phrase}] (2-6) · p.hot: index of the marker to mark in red · p.y (line height, default 520)
SCENES.timeline = p => {
  drift(p, 1.03);   // the row runs close to the frame edges: 1.06 already cuts the outer labels
  const items = p.items, y = p.y || 520, x0 = 260, x1 = 1660, step = (x1 - x0) / Math.max(1, items.length - 1);
  draw(stroke(`M ${x0 - 60} ${y} L ${x1 + 60} ${y}`, 5, FG, .75), .05, .6);
  items.forEach((it, k) => {
    const x = items.length === 1 ? 960 : x0 + k * step, t = at(it.at, .6 + k * .8), hot = k === p.hot;
    const m = dot(x, y, hot ? 18 : 13, hot ? RED : FG); gsap.set(m, { scale: 0 });
    tl.to(m, { scale: 1, duration: .3, ease: TORN ? "steps(3)" : "back.out(2)" }, t);
    // a date never wraps and stays inside the frame (「約公元 200 年」 at the right end lost 「年」 to
    // a second line: box() measures the width first, then the left edge moves right and the line re-wraps)
    const d = box(`<span class="num${hot ? " hot" : ""}" style="white-space:nowrap">${it.date}</span>`, { cx: x, y: y - 150, size: 80 });
    d.style.whiteSpace = "nowrap";
    d.style.left = Math.max(90, Math.min(1830 - d.offsetWidth, x - d.offsetWidth / 2)) + "px"; popIn(d, t);   // 90 px: drift 1.03 pushes the row out
    if (it.text) { const c = box(it.text, { cx: x, y: y + 40, cls: "card", size: 40, w: Math.min(420, step - 20), rot: k % 2 ? 1 : -1 });
      c.style.textAlign = "center"; c.style.left = (x - c.offsetWidth / 2) + "px"; popIn(c, t + .15); }
  });
};

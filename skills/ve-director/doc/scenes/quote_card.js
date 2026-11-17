// quote_card — a full-screen quotation with its source (scripture, a speech, a paper's key sentence).
// p.text · p.by (attribution) · p.at · p.size (default 64) · p.photo: one still {src, rect, rot, cap, push} or two [{...}, {...}].
// Leave rect / rot out to use the layout below: one still upper left, two stills upper left and lower right at
// opposite tilts; the quote strip overlaps them in the middle. Stills without rect slowly push in (push 1.05).
const QUOTE_PHOTOS = {
  1: [{ rect: [90, 150, 780, 439], rot: 3 }],
  2: [{ rect: [70, 90, 760, 428], rot: -3 }, { rect: [1090, 450, 740, 416], rot: 4 }],
};
SCENES.quote_card = p => {
  drift(p);
  const t = at(p.at, .3), ph = p.photo ? [].concat(p.photo) : [];
  if (ph.length > 2) throw new Error("quote_card: photo takes one or two stills");
  ph.forEach((o, i) => {
    const d = QUOTE_PHOTOS[ph.length][i], auto = !o.rect;
    const w = photo({ src: o.src, rect: o.rect || d.rect, rot: o.rot ?? (auto ? d.rot : 0), cap: o.cap });
    photoIn(w, t - .2 + i * .25); sfx("paper", t - .2 + i * .25); capIn(w, t + .2 + i * .25);
    const push = o.push ?? (auto ? 1.05 : null);
    if (push) tl.fromTo(w.inner, { scale: 1 }, { scale: push, duration: D, ease: "none", immediateRender: false }, 0);
  });
  const cx = ph.length === 1 ? 1080 : 960, y = ph.length === 2 ? 400 : 300;
  const q = box(p.text, { cx, y, w: ph.length === 1 ? 1100 : ph.length === 2 ? 1300 : 1400, cls: "card", size: p.size || 64, rot: -1 });
  Object.assign(q.style, { fontFamily: "var(--font-big)", fontWeight: 800, lineHeight: 1.35, textAlign: "center" });
  q.style.left = (cx - q.offsetWidth / 2) + "px"; popIn(q, t); sfx("whoosh", t);
  if (p.by) {
    const b = box(p.by, { cx, y: q.offsetTop + q.offsetHeight + 40, size: 36 });
    // two stills: the second one sits under this line, so lift it above the photos on a paper pill (2026-11-06, 第 60 集 Taher 的出處被蓋掉)
    // the pill is paper-coloured in every palette, so its ink is fixed too: a dark palette's light text vanished on it (2026-11-14 lecture-story)
    if (ph.length === 2) Object.assign(b.style, { zIndex: 22, background: "#f4ecd8", color: "#1d1a17", padding: "6px 18px", borderRadius: "6px" });
    popIn(b, t + .5);
  }
};

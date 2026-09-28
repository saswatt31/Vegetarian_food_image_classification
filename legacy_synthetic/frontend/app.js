/* ============================================================
   ThaliScan — demo logic. Loads the REAL exported artifacts:
     frontend/data/metrics.json      (per-class / category accuracy)
     frontend/data/predictions.json  (per-image softmax top-3)
   produced by the trained model (export_predictions.py).
   ============================================================ */

const CLASS_LABELS = {
  dosa: "Dosa", idli: "Idli", lassi: "Lassi", paneer_curry: "Paneer Curry",
  samosa: "Samosa", veg_biryani: "Veg Biryani", veg_thali: "Veg Thali",
};

let METRICS = null;
let PRED = null;

async function loadJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to load " + url);
  return res.json();
}

const imgURL = (rec) => "assets/img/" + rec.relpath.split("/").slice(1).join("/");

/* ================= hero plate ================= */
function initHero() {
  const rec = PRED.records.find((r) => r.file === "dosa_144.png") || PRED.records[0];
  const el = document.getElementById("heroImgEl");
  el.src = imgURL(rec);
  document.getElementById("heroTrue").textContent =
    (CLASS_LABELS[rec.true] || rec.true) + " · " + (METRICS.class_meta[rec.true] || {}).category;
  const conf = rec.confidence * 100;
  document.getElementById("heroConf").textContent = conf.toFixed(1) + "%";
  const bar = document.getElementById("heroBar");
  requestAnimationFrame(() => (bar.style.width = conf.toFixed(1) + "%"));
  document.querySelector(".plate-verdict .tick").textContent = rec.correct ? "✓" : "!";
  document.querySelector(".plate-verdict").lastChild.textContent = rec.correct
    ? " correct prediction — frozen ResNet-18 head"
    : " misclassification — see the analysis below";
}

/* ================= demo gallery ================= */
function initGallery() {
  const gallery = document.getElementById("gallery");
  const picks = [];
  for (const cls of PRED.classes) {
    picks.push(...PRED.records.filter((r) => r.true === cls && r.correct).slice(0, 2));
  }
  const miss = PRED.records.find((r) => !r.correct);
  if (miss) picks.push(miss);

  gallery.innerHTML = picks
    .map(
      (r, i) => `
    <article class="gal-card ${i === 0 ? "sel" : ""}" data-i="${PRED.records.indexOf(r)}">
      <img src="${imgURL(r)}" alt="${CLASS_LABELS[r.true]}" loading="lazy">
      <div class="gc-body">
        <div class="gc-name">${CLASS_LABELS[r.true]}</div>
        <div class="gc-sub">${r.file}</div>
        <span class="gc-mark ${r.correct ? "ok" : "bad"}">${r.correct ? "✓ " + (r.confidence * 100).toFixed(1) + "%" : "✕ misread"}</span>
      </div>
    </article>`
    )
    .join("");

  gallery.querySelectorAll(".gal-card").forEach((card) => {
    card.addEventListener("click", () => {
      gallery.querySelectorAll(".gal-card").forEach((c) => c.classList.remove("sel"));
      card.classList.add("sel");
      showRecord(PRED.records[+card.dataset.i]);
    });
  });
  return picks;
}

/* ================= filters ================= */
function initFilters(picks) {
  const row = document.getElementById("filters");
  row.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter");
    if (!btn) return;
    row.querySelectorAll(".filter").forEach((b) => b.classList.remove("on"));
    btn.classList.add("on");
    const f = btn.dataset.f;
    const wanted = f === "all" ? picks : picks.filter((r) => (METRICS.class_meta[r.true] || {}).category === f);
    const gallery = document.getElementById("gallery");
    gallery.querySelectorAll(".gal-card").forEach((card) => {
      const rec = PRED.records[+card.dataset.i];
      card.style.display = wanted.includes(rec) ? "" : "none";
    });
  });
}

/* ================= verdict card ================= */
const RING_C = 2 * Math.PI * 52; // r=52 in the SVG

function showRecord(rec) {
  const body = document.querySelector(".verdict-body");
  const ph = document.querySelector(".verdict-placeholder");
  ph.style.display = "none";
  body.hidden = false;

  document.getElementById("vImg").src = imgURL(rec);
  document.getElementById("vTrue").textContent =
    "True: " + (CLASS_LABELS[rec.true] || rec.true);
  const mark = document.getElementById("vMark");
  mark.textContent = rec.correct ? "✓ correct" : "✕ wrong";
  mark.classList.toggle("bad", !rec.correct);

  document.getElementById("vPred").textContent = CLASS_LABELS[rec.pred] || rec.pred;
  const conf = rec.confidence * 100;
  document.getElementById("vConf").textContent = conf.toFixed(1) + "% confidence";

  const ring = document.getElementById("vRing");
  ring.style.strokeDashoffset = RING_C * (1 - rec.confidence);
  document.getElementById("vRingLabel").textContent = conf.toFixed(1) + "%";

  // top-3 + "others" bucket from the real softmax export
  const top3 = rec.top3.map((t) => ({ name: t.class, p: t.prob }));
  const rest = 1 - top3.reduce((s, t) => s + t.p, 0);
  const rows = rest > 0.0005
    ? top3.concat([{ name: "other 4 classes", p: rest }])
    : top3;
  document.getElementById("vTop3").innerHTML = rows
    .map(
      (t, i) => `
      <div class="t3-row ${i === 0 ? "top" : ""}">
        <span class="t3-name">${t.name === "other 4 classes" ? "other 4 classes" : CLASS_LABELS[t.name] || t.name}</span>
        <div class="t3-track"><div class="t3-fill" data-w="${(t.p * 100).toFixed(1)}"></div></div>
        <span class="t3-val">${(t.p * 100).toFixed(1)}%</span>
      </div>`
    )
    .join("");
  requestAnimationFrame(() =>
    document.querySelectorAll("#vTop3 .t3-fill").forEach((b) => (b.style.width = b.dataset.w + "%"))
  );
}

/* ================= menu explorer ================= */
function initMenu() {
  const grid = document.getElementById("menuGrid");
  grid.innerHTML = Object.entries(METRICS.class_meta)
    .map(
      ([cls, meta]) => {
        const pc = METRICS.per_class[cls] || { samples: 16, accuracy: 1 };
        return `
        <article class="menu-card" data-cls="${cls}">
          <img src="assets/img/${cls}/${cls}_144.png" alt="${meta.label}" loading="lazy">
          <div class="mc-body">
            <span class="mc-tag">${meta.category}</span>
            <h3>${meta.label}</h3>
            <p class="mc-blurb">${meta.blurb}</p>
            <div class="mc-acc"><span>test accuracy</span><b>${(pc.accuracy * 100).toFixed(1)}%</b></div>
          </div>
        </article>`;
      }
    )
    .join("");
  grid.querySelectorAll(".menu-card").forEach((card) => {
    card.addEventListener("click", () => {
      const rec = PRED.records.find((r) => r.true === card.dataset.cls && r.correct);
      if (rec) {
        showRecord(rec);
        document.getElementById("demo").scrollIntoView({ behavior: "smooth" });
      }
    });
  });
}

/* ================= results ================= */
function initResults() {
  // category bars
  const rows = Object.entries(METRICS.categories)
    .map(
      ([cat, acc]) => `
      <div class="cat-row">
        <span class="cr-name">${cat}</span>
        <div class="cat-track"><div class="cat-fill" data-w="${(acc * 100).toFixed(1)}"></div></div>
        <span class="cr-val">${(acc * 100).toFixed(1)}%</span>
      </div>`
    )
    .join("");
  document.getElementById("catBars").innerHTML = rows;

  const io = new IntersectionObserver(
    (entries) =>
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        en.target.querySelectorAll(".cat-fill").forEach((b) => (b.style.width = b.dataset.w + "%"));
        io.unobserve(en.target);
      }),
    { threshold: 0.3 }
  );
  io.observe(document.getElementById("catBars"));

  // animated hero counters
  document.querySelectorAll(".stat-n").forEach((el) => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || "";
    const dec = target % 1 !== 0 ? 2 : 0;
    const t0 = performance.now(), dur = 1100;
    (function tick(now) {
      const k = Math.min(1, (now - t0) / dur);
      const eased = 1 - Math.pow(1 - k, 3);
      el.textContent = (target * eased).toFixed(dec) + suffix;
      if (k < 1) requestAnimationFrame(tick);
    })(t0);
  });
}

/* ================= init ================= */
(async function init() {
  METRICS = await loadJSON("data/metrics.json");
  PRED = await loadJSON("data/predictions.json");

  initHero();
  const picks = initGallery();
  initFilters(picks);
  initMenu();
  initResults();
  showRecord(PRED.records.find((r) => r.file === "dosa_144.png") || PRED.records[0]);
})();

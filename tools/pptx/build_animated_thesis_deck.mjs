import fs from 'fs';
import path from 'path';
import process from 'process';

function compact(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function escapeHtml(value) {
  return compact(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function slugify(value, fallback) {
  const slug = compact(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || fallback;
}

function resolveUnderRoot(inputPath, fieldPath, rootDir = process.cwd()) {
  const allowedRoot = path.resolve(rootDir);
  const resolved = path.resolve(inputPath);
  const relative = path.relative(allowedRoot, resolved);
  if (relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))) {
    return resolved;
  }
  throw new Error(`${fieldPath} must resolve inside ${allowedRoot}: ${resolved}`);
}

function readSpec(specPath) {
  const slides = JSON.parse(fs.readFileSync(specPath, 'utf8').replace(/^\uFEFF/, ''));
  if (!Array.isArray(slides) || slides.length === 0) {
    throw new Error('Spec must be a non-empty JSON array');
  }
  return slides.map((slide, index) => ({
    ...slide,
    position: Number(slide.position || index + 1),
    total: Number(slide.total || slides.length),
    title: compact(slide.title),
    takeaway: compact(slide.takeaway),
    bullets: Array.isArray(slide.bullets) ? slide.bullets.map(compact).filter(Boolean) : [],
    speaker_notes: Array.isArray(slide.speaker_notes)
      ? slide.speaker_notes.map(compact).filter(Boolean)
      : compact(slide.speaker_notes)
        ? [compact(slide.speaker_notes)]
        : [],
    code_refs: Array.isArray(slide.code_refs) ? slide.code_refs : [],
    anchor: slugify(slide.anchor || slide.title, `slide-${index + 1}`),
  }));
}

function stepList(items) {
  return items.map((item) => `<li class="step">${escapeHtml(item)}</li>`).join('');
}

function codeCards(refs) {
  if (!refs.length) return '';
  return `
    <div class="code-cards">
      ${refs
        .map(
          (ref) => `
          <article class="code-card step">
            <code>${escapeHtml(ref.path)}</code>
            <span>${escapeHtml(ref.role)}</span>
          </article>`
        )
        .join('')}
    </div>`;
}

function rankingVisual() {
  const rows = [
    ['1', 'C', 'Hierarchy / routing', '0.332606', 'strongest current support'],
    ['2', 'E', 'Network-control energy', '0.175078', 'supportive but split'],
    ['3', 'D', 'Graph repertoire', '0.150619', 'supporting evidence'],
    ['4', 'A', 'Transition-state proxy', '0.148906', 'weak/moderate'],
    ['5', 'B', 'DMDc baseline', '-0.074064', 'negative baseline'],
  ];
  return `
    <div class="ranking-board">
      ${rows
        .map(
          ([rank, layer, name, score, note]) => `
          <div class="rank-row step">
            <b>${rank}</b><strong>${layer}</strong><span>${name}</span><code>${score}</code><em>${note}</em>
          </div>`
        )
        .join('')}
    </div>`;
}

function pipelineVisual(refs) {
  const nodes = [
    ['Data', 'paired placebo/LSD records'],
    ['A-E', 'mechanism metrics'],
    ['Rank', 'signed support scores'],
    ['Export', 'JSON / CSV / XLSX / figures'],
    ['Demo', 'dashboard and defense deck'],
  ];
  return `
    <div class="pipeline">
      ${nodes
        .map(
          ([label, detail], index) => `
          <div class="pipe-node step">
            <span>${index + 1}</span>
            <strong>${label}</strong>
            <small>${detail}</small>
          </div>`
        )
        .join('<div class="pipe-arrow step">-></div>')}
    </div>
    ${codeCards(refs)}`;
}

function eSplitVisual() {
  const metrics = [
    ['+4.70%', 'LSD vs placebo receptor-profile transition-energy reduction', 'supportive'],
    ['+6.94%', 'LSD vs placebo uniform-control transition-energy reduction', 'supportive'],
    ['-34.39%', 'Receptor-prior control vs uniform control', 'opposes'],
    ['-15.08%', 'Receptor-prior control vs random receptor-prior permutations', 'opposes'],
  ];
  return `
    <div class="metric-grid">
      ${metrics
        .map(
          ([value, label, tone]) => `
          <article class="metric-card ${tone} step">
            <strong>${value}</strong>
            <span>${label}</span>
          </article>`
        )
        .join('')}
    </div>`;
}

function roadmapVisual() {
  const steps = ['Robustness', 'Structural graph', 'Receptor maps', 'Schaefer/Yeo', 'Final deck'];
  return `
    <div class="roadmap">
      ${steps
        .map(
          (step, index) => `
          <div class="road-step step">
            <span>${index + 1}</span>
            <strong>${escapeHtml(step)}</strong>
          </div>`
        )
        .join('')}
    </div>`;
}

function defaultVisual(slide) {
  if (slide.layout === 'ranking') return rankingVisual();
  if (slide.layout === 'pipeline') return pipelineVisual(slide.code_refs);
  if (slide.layout === 'file_map') return codeCards(slide.code_refs);
  if (slide.layout === 'e_split') return eSplitVisual();
  if (slide.layout === 'roadmap' || slide.layout === 'next_steps') return roadmapVisual();
  if (slide.code_refs.length) return codeCards(slide.code_refs);
  return `
    <div class="concept-card step">
      <strong>${escapeHtml(slide.title)}</strong>
      <span>${escapeHtml(slide.takeaway || 'Mechanism-ranking evidence with explicit limits.')}</span>
    </div>`;
}

function slideHtml(slide) {
  return `
    <section class="slide" id="${slide.anchor}" data-slide="${slide.position - 1}">
      <header class="slide-header">
        <span>${String(slide.position).padStart(2, '0')} / ${String(slide.total).padStart(2, '0')}</span>
        <h2>${escapeHtml(slide.title)}</h2>
      </header>
      <div class="slide-grid">
        <main>
          ${slide.takeaway ? `<p class="takeaway step">${escapeHtml(slide.takeaway)}</p>` : ''}
          <ul class="bullets">${stepList(slide.bullets)}</ul>
        </main>
        <aside>
          ${defaultVisual(slide)}
        </aside>
      </div>
      ${
        slide.speaker_notes.length
          ? `<footer class="notes"><strong>Speaker notes</strong>${slide.speaker_notes
              .map((note) => `<p>${escapeHtml(note)}</p>`)
              .join('')}</footer>`
          : ''
      }
    </section>`;
}

function buildHtml(slides) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Thesis Defense Deck</title>
  <style>
    :root {
      --bg: #f6f4ef;
      --ink: #19222b;
      --muted: #5f6b73;
      --panel: #fffdf8;
      --line: #d6d0c5;
      --teal: #0b6f6c;
      --rust: #b44b34;
      --blue: #274f7a;
      --green: #2f7d5a;
      --red: #9e2f2f;
      --shadow: 0 28px 80px rgba(25, 34, 43, 0.12);
      --mono: "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      --sans: Aptos, "Segoe UI", system-ui, sans-serif;
      --serif: "Palatino Linotype", Georgia, serif;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink); font-family: var(--sans); }
    body {
      overflow: hidden;
      background:
        linear-gradient(90deg, rgba(11,111,108,0.055) 1px, transparent 1px),
        linear-gradient(180deg, rgba(180,75,52,0.045) 1px, transparent 1px),
        var(--bg);
      background-size: 56px 56px;
    }
    .app { height: 100vh; display: grid; grid-template-columns: 260px 1fr; }
    nav {
      padding: 18px 14px;
      border-right: 1px solid var(--line);
      background: rgba(255,253,248,0.86);
      overflow: auto;
    }
    nav h1 { margin: 0 0 14px; font: 700 18px/1.1 var(--serif); color: var(--teal); }
    nav button {
      width: 100%;
      display: block;
      padding: 8px 10px;
      margin: 0 0 6px;
      border: 1px solid transparent;
      border-radius: 7px;
      background: transparent;
      color: var(--muted);
      text-align: left;
      font: 600 12px/1.25 var(--sans);
      cursor: pointer;
    }
    nav button[aria-current="true"] { background: #eef7f5; border-color: rgba(11,111,108,0.35); color: var(--ink); }
    .stage { position: relative; overflow: hidden; padding: 24px; }
    .slide {
      position: absolute;
      inset: 24px;
      display: none;
      padding: 30px;
      border: 1px solid var(--line);
      border-radius: 12px;
      background: rgba(255,253,248,0.97);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .slide.active { display: grid; grid-template-rows: auto 1fr auto; animation: slideIn 360ms ease-out both; }
    @keyframes slideIn { from { opacity: 0; transform: translateY(18px) scale(0.99); } to { opacity: 1; transform: none; } }
    .slide-header { display: flex; align-items: baseline; gap: 18px; border-bottom: 1px solid var(--line); padding-bottom: 14px; }
    .slide-header span { color: var(--rust); font-weight: 800; letter-spacing: 0.08em; }
    h2 { margin: 0; font: 700 clamp(28px, 3.4vw, 46px)/1.02 var(--serif); color: var(--teal); letter-spacing: 0; }
    .slide-grid { display: grid; grid-template-columns: minmax(0, 0.95fr) minmax(360px, 0.85fr); gap: 28px; align-items: start; padding-top: 22px; min-height: 0; }
    .takeaway {
      margin: 0 0 18px;
      padding: 16px 18px;
      border-left: 5px solid var(--rust);
      border-radius: 0 8px 8px 0;
      background: #f9ece8;
      font: 800 20px/1.35 var(--sans);
    }
    .bullets { margin: 0; padding: 0; display: grid; gap: 12px; list-style: none; }
    .bullets li {
      position: relative;
      padding: 10px 12px 10px 32px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      font-size: 18px;
      line-height: 1.38;
    }
    .bullets li::before {
      content: "";
      position: absolute;
      left: 12px;
      top: 20px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--teal);
    }
    .step { opacity: 0; transform: translateY(14px); transition: opacity 240ms ease, transform 240ms ease; }
    .step.visible { opacity: 1; transform: none; }
    .code-cards, .metric-grid { display: grid; gap: 10px; }
    .code-card, .concept-card, .metric-card {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 10px 24px rgba(25,34,43,0.06);
    }
    .code-card code { display: block; margin-bottom: 6px; font: 700 13px/1.2 var(--mono); color: var(--blue); white-space: normal; }
    .code-card span, .concept-card span, .metric-card span { color: var(--muted); line-height: 1.35; }
    .concept-card strong { display: block; margin-bottom: 10px; font: 800 24px/1.1 var(--serif); color: var(--blue); }
    .ranking-board { display: grid; gap: 8px; }
    .rank-row { display: grid; grid-template-columns: 36px 44px 1fr 90px; gap: 8px; align-items: center; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    .rank-row b { color: var(--rust); font-size: 18px; }
    .rank-row strong { color: var(--teal); font-size: 22px; }
    .rank-row code { font-family: var(--mono); color: var(--blue); }
    .rank-row em { grid-column: 3 / -1; color: var(--muted); font-size: 13px; font-style: normal; }
    .pipeline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
    .pipe-node { width: 116px; min-height: 102px; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    .pipe-node span, .road-step span { display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; background: var(--teal); color: #fff; font-weight: 800; }
    .pipe-node strong, .road-step strong { display: block; margin: 8px 0 4px; color: var(--blue); }
    .pipe-node small { color: var(--muted); }
    .pipe-arrow { color: var(--rust); font-weight: 900; }
    .metric-card strong { display: block; font: 900 32px/1 var(--sans); margin-bottom: 8px; }
    .metric-card.supportive strong { color: var(--green); }
    .metric-card.opposes strong { color: var(--red); }
    .roadmap { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
    .road-step { min-height: 120px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    .notes {
      display: none;
      margin-top: 12px;
      padding: 12px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }
    body.show-notes .notes { display: block; }
    .controls {
      position: fixed;
      right: 24px;
      bottom: 18px;
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255,253,248,0.92);
      box-shadow: 0 12px 28px rgba(25,34,43,0.12);
    }
    .controls button { border: 0; border-radius: 999px; background: var(--teal); color: #fff; padding: 8px 12px; font-weight: 800; cursor: pointer; }
    .controls span { padding: 0 6px; color: var(--muted); font-size: 12px; }
    .progress { position: fixed; left: 0; right: 0; bottom: 0; height: 4px; background: rgba(11,111,108,0.16); }
    .progress > div { height: 100%; width: 0%; background: var(--teal); transition: width 180ms ease; }
    @media (max-width: 980px) {
      body { overflow: auto; }
      .app { display: block; }
      nav { display: none; }
      .stage { min-height: 100vh; }
      .slide { position: static; min-height: calc(100vh - 48px); }
      .slide-grid { grid-template-columns: 1fr; }
      .roadmap { grid-template-columns: 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      .slide.active, .step { animation: none; transition: none; }
    }
    @media print {
      body { overflow: visible; background: #fff; }
      .app { display: block; }
      nav, .controls, .progress { display: none; }
      .stage { padding: 0; }
      .slide { display: block !important; position: static; min-height: 100vh; page-break-after: always; box-shadow: none; border-radius: 0; }
      .step { opacity: 1 !important; transform: none !important; }
    }
  </style>
</head>
<body>
  <div class="app">
    <nav aria-label="Slide navigation">
      <h1>Thesis Defense</h1>
      ${slides
        .map(
          (slide, index) => `<button type="button" data-target="${index}">${String(slide.position).padStart(2, '0')}. ${escapeHtml(slide.title)}</button>`
        )
        .join('')}
    </nav>
    <main class="stage">
      ${slides.map(slideHtml).join('')}
    </main>
  </div>
  <div class="controls">
    <button type="button" id="prev">Prev</button>
    <span id="counter"></span>
    <button type="button" id="next">Next</button>
    <button type="button" id="notes">Notes</button>
  </div>
  <div class="progress"><div id="progress"></div></div>
  <script>
    const slides = Array.from(document.querySelectorAll('.slide'));
    const navButtons = Array.from(document.querySelectorAll('nav button'));
    let slideIndex = 0;
    let stepIndex = 0;

    function visibleSteps(slide) {
      return Array.from(slide.querySelectorAll('.step'));
    }

    function render() {
      slides.forEach((slide, index) => {
        const active = index === slideIndex;
        slide.classList.toggle('active', active);
        visibleSteps(slide).forEach((step, stepNumber) => {
          step.classList.toggle('visible', active && stepNumber < stepIndex);
        });
      });
      navButtons.forEach((button, index) => {
        button.setAttribute('aria-current', index === slideIndex ? 'true' : 'false');
      });
      document.getElementById('counter').textContent = (slideIndex + 1) + ' / ' + slides.length + ' - step ' + stepIndex;
      const denominator = Math.max(1, slides.length - 1);
      document.getElementById('progress').style.width = ((slideIndex / denominator) * 100).toFixed(2) + '%';
    }

    function next() {
      const steps = visibleSteps(slides[slideIndex]);
      if (stepIndex < steps.length) {
        stepIndex += 1;
      } else if (slideIndex < slides.length - 1) {
        slideIndex += 1;
        stepIndex = 1;
      }
      render();
    }

    function prev() {
      if (stepIndex > 1) {
        stepIndex -= 1;
      } else if (slideIndex > 0) {
        slideIndex -= 1;
        stepIndex = Math.max(1, visibleSteps(slides[slideIndex]).length);
      }
      render();
    }

    document.getElementById('next').addEventListener('click', next);
    document.getElementById('prev').addEventListener('click', prev);
    document.getElementById('notes').addEventListener('click', () => document.body.classList.toggle('show-notes'));
    navButtons.forEach((button) => button.addEventListener('click', () => {
      slideIndex = Number(button.dataset.target);
      stepIndex = 1;
      render();
    }));
    document.addEventListener('keydown', (event) => {
      if (['ArrowRight', 'PageDown', ' '].includes(event.key)) {
        event.preventDefault();
        next();
      }
      if (['ArrowLeft', 'PageUp', 'Backspace'].includes(event.key)) {
        event.preventDefault();
        prev();
      }
      if (event.key.toLowerCase() === 'n') {
        document.body.classList.toggle('show-notes');
      }
      if (event.key.toLowerCase() === 'f') {
        document.documentElement.requestFullscreen?.();
      }
    });
    stepIndex = 1;
    render();
  </script>
</body>
</html>`;
}

function main() {
  const [specPathArg, outputPathArg] = process.argv.slice(2);
  if (!specPathArg || !outputPathArg) {
    throw new Error('Usage: node build_animated_thesis_deck.mjs <spec.json> <output.html>');
  }
  const root = process.cwd();
  const specPath = resolveUnderRoot(specPathArg, 'specPath', root);
  const outputPath = resolveUnderRoot(outputPathArg, 'outputPath', root);
  const slides = readSpec(specPath);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, buildHtml(slides), 'utf8');
  if (!fs.existsSync(outputPath)) {
    throw new Error(`HTML build completed without output file: ${outputPath}`);
  }
  console.log(`wrote ${outputPath}`);
}

main();

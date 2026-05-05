import fs from 'fs';
import path from 'path';
import process from 'process';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const PptxGenJS = require('pptxgenjs');
const { imageSizingContain } = require('./pptxgenjs_helpers/image');
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require('./pptxgenjs_helpers/layout');

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenAI';
pptx.company = 'OpenAI';
pptx.subject = 'Defense presentation';
pptx.title = 'Defense presentation';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};

const COLORS = {
  bg: 'F6F1E8',
  panel: 'FFFDF8',
  panelSoft: 'F2EBDD',
  title: '173857',
  text: '172433',
  muted: '5B6978',
  accent: 'C59F5A',
  line: 'D6CCBC',
  lineDark: 'B7AC97',
};

const PAGE = {
  w: 13.333,
  h: 7.5,
  marginX: 0.48,
  marginY: 0.38,
  gap: 0.28,
};

function readSpec(specPath) {
  const text = fs.readFileSync(specPath, 'utf8').replace(/^\uFEFF/, '');
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) {
    throw new Error('Spec must be a JSON array of slide objects');
  }
  return parsed;
}

function compact(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function toBullets(value) {
  if (!Array.isArray(value)) return [];
  return value.map(compact).filter(Boolean);
}

function resolveImagePath(specPath, imagePath) {
  if (!imagePath) return null;
  const raw = String(imagePath);
  return path.isAbsolute(raw) ? raw : path.resolve(path.dirname(specPath), raw);
}

function estimateTextHeight(text, width, fontSize, lineHeight = 1.08) {
  const clean = compact(text);
  if (!clean) return 0;
  const avgCharsPerLine = Math.max(18, Math.floor(width * 9.5));
  const lineCount = Math.max(1, Math.ceil(clean.length / avgCharsPerLine));
  return lineCount * (fontSize / 72) * lineHeight + 0.08;
}

function addBackground(slide) {
  slide.background = { color: COLORS.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: PAGE.w,
    h: PAGE.h,
    line: { color: COLORS.bg, transparency: 100 },
    fill: { color: COLORS.bg },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: PAGE.w,
    h: 0.16,
    line: { color: COLORS.accent, transparency: 100 },
    fill: { color: COLORS.accent },
  });
}

function addHeader(slide, slideData) {
  const title = compact(slideData.title);
  const position = Number(slideData.position || 0);
  const total = Number(slideData.total || 0);
  slide.addText(title, {
    x: PAGE.marginX,
    y: 0.34,
    w: PAGE.w - PAGE.marginX * 2 - 1.0,
    h: 0.62,
    fontFace: 'Aptos Display',
    fontSize: 24,
    bold: true,
    color: COLORS.title,
    margin: 0,
    breakLine: false,
  });
  slide.addText(total > 0 ? `${position}/${total}` : '', {
    x: PAGE.w - PAGE.marginX - 0.8,
    y: 0.38,
    w: 0.8,
    h: 0.34,
    fontFace: 'Aptos',
    fontSize: 11,
    color: COLORS.muted,
    align: 'right',
    margin: 0,
  });
}

function addTakeaway(slide, slideData, box) {
  const takeaway = compact(slideData.takeaway);
  if (!takeaway) return box.y;
  const height = Math.max(0.52, estimateTextHeight(takeaway, box.w - 0.3, 13, 1.08));
  slide.addShape(pptx.ShapeType.roundRect, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: height,
    rectRadius: 0.12,
    line: { color: COLORS.lineDark, pt: 1 },
    fill: { color: COLORS.panelSoft },
  });
  slide.addText(takeaway, {
    x: box.x + 0.14,
    y: box.y + 0.08,
    w: box.w - 0.28,
    h: height - 0.12,
    fontFace: 'Aptos',
    fontSize: 13,
    bold: true,
    color: COLORS.text,
    margin: 0,
    valign: 'mid',
  });
  return box.y + height + 0.16;
}

function addBullets(slide, bullets, box) {
  let y = box.y;
  for (const bullet of bullets) {
    const line = compact(bullet);
    if (!line) continue;
    const h = Math.max(0.26, estimateTextHeight(line, box.w - 0.28, 12, 1.06));
    slide.addText(line, {
      x: box.x + 0.02,
      y,
      w: box.w,
      h,
      fontFace: 'Aptos',
      fontSize: 12,
      color: COLORS.text,
      margin: 0,
      bullet: { indent: 14 },
      hanging: 3,
    });
    y += h + 0.06;
  }
  return y;
}

function addFooter(slide, slideData, y, width) {
  const citation = compact(slideData.citation);
  const note = compact(slideData.note);
  if (!citation && !note) return;
  const footer = [note, citation].filter(Boolean).join('  ');
  const footerHeight = Math.max(0.3, estimateTextHeight(footer, width, 9.5, 1.04));
  slide.addText(footer, {
    x: PAGE.marginX,
    y,
    w: width,
    h: footerHeight,
    fontFace: 'Aptos',
    fontSize: 9.5,
    color: COLORS.muted,
    italic: true,
    margin: 0,
  });
}

function addImagePanel(slide, slideData, imagePath, box) {
  if (!imagePath) return false;
  if (!fs.existsSync(imagePath)) {
    console.warn(`Missing image for slide ${slideData.position}: ${imagePath}`);
    return false;
  }
  slide.addShape(pptx.ShapeType.roundRect, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    rectRadius: 0.12,
    line: { color: COLORS.line, pt: 1 },
    fill: { color: COLORS.panel },
  });
  const imageBox = {
    x: box.x + 0.12,
    y: box.y + 0.12,
    w: box.w - 0.24,
    h: box.h - 0.56,
  };
  slide.addImage({
    path: imagePath,
    ...imageSizingContain(imagePath, imageBox.x, imageBox.y, imageBox.w, imageBox.h),
  });
  const captionParts = [compact(slideData.image_caption), compact(slideData.image_alt)].filter(Boolean);
  const caption = captionParts.join(' - ');
  if (caption) {
    slide.addText(caption, {
      x: box.x + 0.12,
      y: box.y + box.h - 0.36,
      w: box.w - 0.24,
      h: 0.26,
      fontFace: 'Aptos',
      fontSize: 9.5,
      color: COLORS.muted,
      align: 'left',
      margin: 0,
      italic: true,
    });
  }
  return true;
}

function buildSlide(slideData, specPath) {
  const slide = pptx.addSlide();
  addBackground(slide);
  addHeader(slide, slideData);

  const imagePath = resolveImagePath(specPath, slideData.image_path);
  const hasImage = Boolean(imagePath);
  const bodyTop = 1.2;
  const contentBottom = 6.98;
  const contentHeight = contentBottom - bodyTop;

  if (hasImage) {
    const leftW = 6.0;
    const rightW = PAGE.w - PAGE.marginX * 2 - leftW - PAGE.gap;
    const left = { x: PAGE.marginX, y: bodyTop, w: leftW, h: contentHeight };
    const right = { x: PAGE.marginX + leftW + PAGE.gap, y: bodyTop, w: rightW, h: contentHeight };
    let y = addTakeaway(slide, slideData, { ...left, h: 0 });
    y = addBullets(slide, toBullets(slideData.bullets), { x: left.x, y: y + 0.02, w: left.w });
    const footerY = Math.min(contentBottom - 0.28, y + 0.16);
    addFooter(slide, slideData, footerY, left.w);
    addImagePanel(slide, slideData, imagePath, right);
  } else {
    const wide = { x: PAGE.marginX, y: bodyTop, w: PAGE.w - PAGE.marginX * 2, h: contentHeight };
    let y = addTakeaway(slide, slideData, wide);
    y = addBullets(slide, toBullets(slideData.bullets), { x: wide.x, y: y + 0.02, w: wide.w });
    addFooter(slide, slideData, Math.min(contentBottom - 0.28, y + 0.2), wide.w);
  }

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

async function main() {
  const [specPathArg, outputPathArg] = process.argv.slice(2);
  if (!specPathArg || !outputPathArg) {
    throw new Error('Usage: node build_defense_deck.mjs <spec.json> <output.pptx>');
  }

  const specPath = path.resolve(specPathArg);
  const outputPath = path.resolve(outputPathArg);
  const slides = readSpec(specPath);

  if (slides.length === 0) {
    throw new Error('Spec contained no slides');
  }

  for (const slideData of slides) {
    buildSlide(slideData, specPath);
  }

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  await pptx.writeFile({ fileName: outputPath });
  if (!fs.existsSync(outputPath)) {
    throw new Error(`PPTX build completed without output file: ${outputPath}`);
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exitCode = 1;
});

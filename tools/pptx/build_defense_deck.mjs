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

async function readSpec(specPath) {
  const text = (await fs.promises.readFile(specPath, 'utf8')).replace(/^\uFEFF/, '');
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) {
    throw new Error('Spec must be a JSON array of slide objects');
  }
  return validateSpec(parsed, specPath);
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

function resolveExistingFileUnderRoot(inputPath, fieldPath, rootDir = process.cwd()) {
  const resolved = resolveUnderRoot(inputPath, fieldPath, rootDir);
  const stats = fs.statSync(resolved);
  if (!stats.isFile()) {
    throw new Error(`${fieldPath} must be a file: ${resolved}`);
  }
  const realRoot = fs.realpathSync(rootDir);
  const realPath = fs.realpathSync(resolved);
  const relative = path.relative(realRoot, realPath);
  if (relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))) {
    return realPath;
  }
  throw new Error(`${fieldPath} must resolve inside ${realRoot}: ${realPath}`);
}

function compact(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

function validateStringField(value, fieldPath, { required = false } = {}) {
  if (value === undefined || value === null) {
    if (required) {
      throw new Error(`${fieldPath} is required`);
    }
    return null;
  }
  if (typeof value !== 'string') {
    throw new Error(`${fieldPath} must be a string`);
  }
  const clean = compact(value);
  if (required && !clean) {
    throw new Error(`${fieldPath} must be a non-empty string`);
  }
  return clean || null;
}

function validateBullets(value, fieldPath) {
  if (value === undefined || value === null) {
    return [];
  }
  if (!Array.isArray(value)) {
    throw new Error(`${fieldPath} must be an array of strings`);
  }
  return value.map((item, index) => {
    const clean = validateStringField(item, `${fieldPath}[${index}]`, { required: true });
    return clean;
  });
}

function validateSpeakerNotes(value, fieldPath) {
  if (value === undefined || value === null) {
    return [];
  }
  if (typeof value === 'string') {
    const clean = compact(value);
    return clean ? [clean] : [];
  }
  if (!Array.isArray(value)) {
    throw new Error(`${fieldPath} must be a string or an array of strings`);
  }
  return value.map((item, index) => validateStringField(item, `${fieldPath}[${index}]`, { required: true }));
}

function validateOptionalInteger(value, fieldPath) {
  if (value === undefined || value === null || value === '') {
    return null;
  }
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0) {
    throw new Error(`${fieldPath} must be a non-negative integer`);
  }
  return number;
}

function warnIfPotentiallyStaleClaim(slideData, index) {
  const text = [
    slideData.title,
    slideData.takeaway,
    ...(Array.isArray(slideData.bullets) ? slideData.bullets : []),
    slideData.citation,
    slideData.note,
  ].map(compact).join(' ');
  if (/\b57\s+tests passed\b/i.test(text) || /\b2026-04-15\b/.test(text)) {
    console.warn(
      `Potential stale validation claim in slides[${index}]; prefer regenerated validation metadata over fixed dated prose.`
    );
  }
  const hasCompletedHoldoutClaim = /\bsubject-disjoint\s+held-out\s+validation\s+has\s+been\s+completed\b/i.test(text);
  const hasQualifiedInternalClaim =
    /\bapproved\b/i.test(text) &&
    /\binternal\b/i.test(text) &&
    /\bnot\s+external\b/i.test(text) &&
    !/\bcandidate\b/i.test(text);
  if (hasCompletedHoldoutClaim && !hasQualifiedInternalClaim) {
    console.warn(
      `Potential stale held-out validation claim in slides[${index}]; confirm Stage 2/3 split metadata before presenting this as completed.`
    );
  }
  if (/\bcandidate\b/i.test(text) && /\bheld-out\s+validation\s+has\s+been\s+completed\b/i.test(text)) {
    throw new Error(
      `Invalid candidate split validation claim in slides[${index}]; candidate splits cannot be presented as completed held-out validation.`
    );
  }
  const hasExternalValidationClaim =
    /\bexternal\s+validation\b/i.test(text) &&
    !/\b(no|not|without)\s+external\s+validation\b/i.test(text) &&
    !/\bnot\s+external\s+or\s+clinical\s+validation\b/i.test(text);
  if (hasExternalValidationClaim) {
    console.warn(
      `Potential unsupported external validation claim in slides[${index}]; current evidence supports internal CV5 validation only.`
    );
  }
  const hasClinicalValidationClaim =
    /\bclinical\s+validation\b/i.test(text) &&
    !/\b(no|not|without)\s+clinical\s+validation\b/i.test(text) &&
    !/\bnot\s+external\s+or\s+clinical\s+validation\b/i.test(text);
  if (hasClinicalValidationClaim) {
    console.warn(
      `Potential unsupported clinical validation claim in slides[${index}]; current evidence is not clinical validation.`
    );
  }
  if (/\bvalidated\s+model\b/i.test(text)) {
    console.warn(
      `Potential overclaim in slides[${index}]; prefer preliminary internal validation of a surrogate over "validated model".`
    );
  }
}

function validateSpec(slides, specPath, allowedRoot = path.dirname(specPath)) {
  if (slides.length === 0) {
    throw new Error('Spec contained no slides');
  }
  return slides.map((slideData, index) => {
    if (!slideData || typeof slideData !== 'object' || Array.isArray(slideData)) {
      throw new Error(`slides[${index}] must be an object`);
    }
    const validated = { ...slideData };
    validated.title = validateStringField(slideData.title, `slides[${index}].title`, { required: true });
    validated.bullets = validateBullets(slideData.bullets, `slides[${index}].bullets`);
    validated.speaker_notes = validateSpeakerNotes(slideData.speaker_notes, `slides[${index}].speaker_notes`);
    for (const fieldName of ['takeaway', 'image_alt', 'image_caption', 'citation', 'note', 'anchor']) {
      validated[fieldName] = validateStringField(slideData[fieldName], `slides[${index}].${fieldName}`) || '';
    }
    validated.position = validateOptionalInteger(slideData.position, `slides[${index}].position`) ?? slideData.position;
    validated.total = validateOptionalInteger(slideData.total, `slides[${index}].total`) ?? slideData.total;
    warnIfPotentiallyStaleClaim(validated, index);

    const imagePath = validateStringField(slideData.image_path, `slides[${index}].image_path`);
    validated.image_path = imagePath;
    if (imagePath) {
      const resolvedImagePath = resolveImagePath(specPath, imagePath, allowedRoot);
      validated.image_path = resolvedImagePath;
      if (!resolvedImagePath || !fs.existsSync(resolvedImagePath)) {
        if (slideData.allow_missing_images === true) {
          console.warn(`Missing image for slide ${index + 1}: ${resolvedImagePath}`);
        } else {
          throw new Error(
            `slides[${index}].image_path does not exist: ${resolvedImagePath}. Set allow_missing_images=true only for an intentional placeholder.`
          );
        }
      } else {
        validated.image_path = resolveExistingFileUnderRoot(
          resolvedImagePath,
          `slides[${index}].image_path`,
          allowedRoot
        );
      }
    }
    return validated;
  });
}

function toBullets(value) {
  if (!Array.isArray(value)) return [];
  return value.map(compact).filter(Boolean);
}

function resolveImagePath(specPath, imagePath, allowedRoot = path.dirname(specPath)) {
  if (!imagePath) return null;
  const raw = String(imagePath);
  const resolved = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(path.dirname(specPath), raw);
  return resolveUnderRoot(resolved, 'image_path', allowedRoot);
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
  if (Array.isArray(slideData.speaker_notes) && slideData.speaker_notes.length) {
    slide.addNotes(slideData.speaker_notes.join('\n\n'));
  }
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

  const allowedRoot = path.resolve(process.cwd());
  const specPath = resolveExistingFileUnderRoot(specPathArg, 'specPath', allowedRoot);
  const outputPath = resolveUnderRoot(outputPathArg, 'outputPath', allowedRoot);
  if (path.extname(specPath).toLowerCase() !== '.json') {
    throw new Error('specPath must be a .json file');
  }
  const slides = await readSpec(specPath);

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

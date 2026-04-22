(() => {
  const now = new Date().toISOString();

  const cleanText = (t) => (t || '').replace(/\s+/g, ' ').trim();
  const trunc = (s, n = 120) => cleanText(s).slice(0, n);
  const pxNum = (v) => {
    if (v == null) return null;
    const m = String(v).match(/-?\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : null;
  };
  const round = (n, p = 2) => Number(Number(n).toFixed(p));
  const toCountMap = () => Object.create(null);
  const inc = (obj, key, by = 1) => {
    if (!key) return;
    obj[key] = (obj[key] || 0) + by;
  };
  const sortedEntries = (obj) => Object.entries(obj).sort((a, b) => b[1] - a[1]);

  const isTransparent = (v) => {
    const s = String(v || '').trim().toLowerCase();
    return !s || s === 'transparent' || s === 'rgba(0, 0, 0, 0)' || s === 'rgba(0,0,0,0)';
  };

  const parseRgb = (value) => {
    if (!value) return null;
    const s = String(value).trim();
    if (s.startsWith('#')) {
      let hex = s.slice(1);
      if (hex.length === 3) hex = hex.split('').map((x) => x + x).join('');
      if (hex.length === 6 || hex.length === 8) {
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        const a = hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1;
        return { r, g, b, a, format: 'hex' };
      }
    }
    const m = s.match(/rgba?\(([^)]+)\)/i);
    if (!m) return null;
    const parts = m[1].split(',').map((x) => x.trim());
    if (parts.length < 3) return null;
    const r = parseFloat(parts[0]);
    const g = parseFloat(parts[1]);
    const b = parseFloat(parts[2]);
    const a = parts[3] != null ? parseFloat(parts[3]) : 1;
    if ([r, g, b].some((x) => Number.isNaN(x))) return null;
    return { r, g, b, a, format: 'rgb' };
  };

  const toHex = (value) => {
    const rgb = parseRgb(value);
    if (!rgb) return value || null;
    const hex = [rgb.r, rgb.g, rgb.b]
      .map((n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0'))
      .join('')
      .toUpperCase();
    return `#${hex}`;
  };

  const normColor = (value) => {
    if (!value || isTransparent(value)) return null;
    return toHex(value);
  };

  const luminance = (hex) => {
    const rgb = parseRgb(hex);
    if (!rgb) return null;
    const toLin = (c) => {
      c /= 255;
      return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
    };
    const r = toLin(rgb.r);
    const g = toLin(rgb.g);
    const b = toLin(rgb.b);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const contrastRatio = (a, b) => {
    const la = luminance(a);
    const lb = luminance(b);
    if (la == null || lb == null) return null;
    const lighter = Math.max(la, lb);
    const darker = Math.min(la, lb);
    return round((lighter + 0.05) / (darker + 0.05), 2);
  };

  const uniqueBy = (arr, keyFn) => {
    const seen = new Set();
    const out = [];
    for (const item of arr) {
      const key = keyFn(item);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(item);
    }
    return out;
  };

  const cssVars = (() => {
    const s = getComputedStyle(document.documentElement);
    return Object.fromEntries(
      Array.from(s)
        .filter((k) => k.startsWith('--'))
        .map((k) => [k, s.getPropertyValue(k).trim()])
        .filter(([, v]) => v)
    );
  })();

  const allEls = [...document.querySelectorAll('*')];
  const visibleEls = allEls.filter((el) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && parseFloat(s.opacity || '1') > 0 && r.width > 0 && r.height > 0;
  });

  const bodyStyle = getComputedStyle(document.body);
  const htmlStyle = getComputedStyle(document.documentElement);

  const counts = {
    textColors: toCountMap(),
    bgColors: toCountMap(),
    borderColors: toCountMap(),
    fontFamilies: toCountMap(),
    fontSizes: toCountMap(),
    fontWeights: toCountMap(),
    lineHeights: toCountMap(),
    letterSpacings: toCountMap(),
    radii: toCountMap(),
    shadows: toCountMap(),
    spacing: toCountMap(),
    gaps: toCountMap(),
    typographyCombos: toCountMap(),
    maxWidths: toCountMap(),
  };

  const samples = {
    headings: [],
    paragraphs: [],
    buttons: [],
    inputs: [],
    cards: [],
    links: [],
    containers: [],
    navs: [],
    badges: [],
  };

  const sampleLimit = 60;

  const pushSample = (bucket, value, keyFields = ['tag', 'className', 'text']) => {
    if (samples[bucket].length >= sampleLimit) return;
    const key = keyFields.map((k) => value[k] || '').join('|');
    if (samples[bucket].some((x) => keyFields.map((k) => x[k] || '').join('|') === key)) return;
    samples[bucket].push(value);
  };

  for (const el of visibleEls) {
    const s = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    const tag = el.tagName.toLowerCase();
    const text = trunc(el.innerText || el.textContent || '');
    const role = (el.getAttribute('role') || '').toLowerCase();
    const className = typeof el.className === 'string' ? el.className : '';
    const id = el.id || '';

    const color = normColor(s.color);
    const backgroundColor = normColor(s.backgroundColor);
    const borderColor = normColor(s.borderColor);
    const fontFamily = s.fontFamily;
    const fontSize = s.fontSize;
    const fontWeight = s.fontWeight;
    const lineHeight = s.lineHeight;
    const letterSpacing = s.letterSpacing;
    const borderRadius = s.borderRadius;
    const boxShadow = s.boxShadow;
    const gap = s.gap;
    const maxWidth = s.maxWidth;

    if (color) inc(counts.textColors, color);
    if (backgroundColor) inc(counts.bgColors, backgroundColor);
    if (borderColor) inc(counts.borderColors, borderColor);
    if (fontFamily) inc(counts.fontFamilies, fontFamily);
    if (fontSize) inc(counts.fontSizes, fontSize);
    if (fontWeight) inc(counts.fontWeights, fontWeight);
    if (lineHeight) inc(counts.lineHeights, lineHeight);
    if (letterSpacing) inc(counts.letterSpacings, letterSpacing);
    if (borderRadius && borderRadius !== '0px') inc(counts.radii, borderRadius);
    if (boxShadow && boxShadow !== 'none') inc(counts.shadows, boxShadow);
    if (gap && gap !== 'normal' && gap !== '0px') inc(counts.gaps, gap);
    if (maxWidth && maxWidth !== 'none') inc(counts.maxWidths, maxWidth);

    [s.paddingTop, s.paddingRight, s.paddingBottom, s.paddingLeft, s.marginTop, s.marginRight, s.marginBottom, s.marginLeft]
      .forEach((v) => {
        if (v && v !== '0px' && v !== 'auto') inc(counts.spacing, v);
      });

    inc(counts.typographyCombos, JSON.stringify({ fontFamily, fontSize, fontWeight, lineHeight, letterSpacing }));

    const common = {
      tag,
      role,
      id,
      className,
      text,
      href: tag === 'a' ? el.getAttribute('href') || '' : '',
      color,
      backgroundColor,
      borderColor,
      fontFamily,
      fontSize,
      fontWeight,
      lineHeight,
      letterSpacing,
      borderRadius,
      boxShadow,
      padding: s.padding,
      margin: s.margin,
      gap: s.gap,
      display: s.display,
      width: s.width,
      height: s.height,
      maxWidth: s.maxWidth,
      minHeight: s.minHeight,
      justifyContent: s.justifyContent,
      alignItems: s.alignItems,
      gridTemplateColumns: s.gridTemplateColumns,
      rect: { width: Math.round(rect.width), height: Math.round(rect.height) },
      selectors: {
        id: id ? `#${id}` : '',
        classes: className ? className.split(/\s+/).filter(Boolean).slice(0, 5).map((c) => `.${c}`) : [],
      },
    };

    if (/^h[1-6]$/.test(tag)) pushSample('headings', common, ['tag', 'text', 'fontSize']);
    if (['p', 'small', 'label'].includes(tag)) pushSample('paragraphs', common, ['tag', 'text', 'fontSize']);

    const isButtonLike = tag === 'button' || role === 'button' || (tag === 'a' && /btn|button|cta|primary|secondary/i.test(className)) || (tag === 'input' && ['button', 'submit'].includes((el.type || '').toLowerCase()));
    if (isButtonLike) pushSample('buttons', common, ['tag', 'className', 'backgroundColor', 'color']);

    const isInputLike = ['input', 'textarea', 'select'].includes(tag);
    if (isInputLike) pushSample('inputs', common, ['tag', 'className', 'borderColor', 'backgroundColor']);

    if (tag === 'a') pushSample('links', common, ['text', 'href', 'color']);
    if (tag === 'nav' || role === 'navigation' || /nav|navbar|header-menu/i.test(className)) pushSample('navs', common, ['tag', 'className']);
    if (/badge|chip|pill|tag/i.test(className)) pushSample('badges', common, ['className', 'backgroundColor', 'color']);

    const containerLike = s.display.includes('flex') || s.display.includes('grid') || pxNum(s.maxWidth) > 360;
    if (containerLike) pushSample('containers', common, ['className', 'maxWidth', 'display']);

    const hasCardLikeVisual = !!backgroundColor && !isTransparent(backgroundColor) && backgroundColor !== normColor(bodyStyle.backgroundColor) && (borderRadius !== '0px' || (boxShadow && boxShadow !== 'none') || borderColor);
    if ((['div', 'section', 'article', 'aside', 'li'].includes(tag)) && hasCardLikeVisual) pushSample('cards', common, ['className', 'backgroundColor', 'borderRadius', 'boxShadow']);
  }

  const topTextColors = sortedEntries(counts.textColors).slice(0, 16);
  const topBgColors = sortedEntries(counts.bgColors).slice(0, 16);
  const topBorderColors = sortedEntries(counts.borderColors).slice(0, 16);
  const topFonts = sortedEntries(counts.fontFamilies).slice(0, 8);
  const topFontSizes = sortedEntries(counts.fontSizes).slice(0, 12);
  const topRadii = sortedEntries(counts.radii).slice(0, 10);
  const topSpacing = sortedEntries(counts.spacing).slice(0, 16);
  const topShadows = sortedEntries(counts.shadows).slice(0, 10);
  const topGaps = sortedEntries(counts.gaps).slice(0, 12);
  const topMaxWidths = sortedEntries(counts.maxWidths).slice(0, 12);
  const topTypoCombos = sortedEntries(counts.typographyCombos)
    .slice(0, 16)
    .map(([k, count]) => ({ count, style: JSON.parse(k) }));

  const bodyBg = normColor(bodyStyle.backgroundColor) || normColor(htmlStyle.backgroundColor) || topBgColors[0]?.[0] || '#FFFFFF';
  const bodyText = normColor(bodyStyle.color) || topTextColors[0]?.[0] || '#111111';
  const distinctText = uniqueBy(topTextColors.map(([c, count]) => ({ color: c, count })), (x) => x.color).map((x) => x.color);
  const distinctBg = uniqueBy(topBgColors.map(([c, count]) => ({ color: c, count })), (x) => x.color).map((x) => x.color);
  const distinctBorder = uniqueBy(topBorderColors.map(([c, count]) => ({ color: c, count })), (x) => x.color).map((x) => x.color);

  const links = samples.links;
  const buttons = samples.buttons;
  const cards = samples.cards;
  const inputs = samples.inputs;
  const headings = samples.headings;
  const paragraphs = samples.paragraphs;
  const containers = samples.containers;

  const linkColor = links.find((x) => x.color && x.color !== bodyText)?.color || distinctText.find((c) => c !== bodyText) || bodyText;
  const primaryButton = buttons.find((b) => b.backgroundColor && b.backgroundColor !== bodyBg) || buttons[0] || null;
  const secondaryButton = buttons.find((b) => (!b.backgroundColor || b.backgroundColor === bodyBg) && b.borderColor) || buttons.find((b) => b.backgroundColor !== primaryButton?.backgroundColor) || null;
  const cardSample = cards[0] || null;
  const inputSample = inputs[0] || null;
  const navSample = samples.navs[0] || null;
  const badgeSample = samples.badges[0] || null;

  const guessAccent = primaryButton?.backgroundColor || linkColor || distinctBg.find((c) => c !== bodyBg) || distinctText.find((c) => c !== bodyText) || bodyText;
  const guessSurface = cardSample?.backgroundColor || distinctBg.find((c) => c !== bodyBg) || bodyBg;
  const guessSecondaryText = distinctText.find((c) => c !== bodyText) || bodyText;
  const guessBorder = inputSample?.borderColor || distinctBorder[0] || guessSecondaryText;
  const guessMutedSurface = distinctBg.find((c) => c !== bodyBg && c !== guessSurface) || guessSurface;

  const chooseSpacingScale = (() => {
    const uniq = uniqueBy(
      topSpacing
        .map(([raw, count]) => ({ raw, count, n: pxNum(raw) }))
        .filter((x) => x.n && x.n > 0)
        .sort((a, b) => a.n - b.n),
      (x) => Math.round(x.n * 10) / 10
    );
    const pick = (fallback, idx) => uniq[idx]?.raw || fallback;
    return {
      xs: pick('4px', 0),
      sm: pick('8px', 1),
      md: pick('12px', 2),
      lg: pick('16px', 3),
      xl: pick('24px', 4),
      '2xl': pick('32px', 5),
    };
  })();

  const chooseRadiusScale = (() => {
    const uniq = uniqueBy(
      topRadii
        .map(([raw, count]) => ({ raw, count, n: pxNum(raw) }))
        .filter((x) => x.n && x.n > 0)
        .sort((a, b) => a.n - b.n),
      (x) => Math.round(x.n * 10) / 10
    );
    return {
      sm: uniq[0]?.raw || '4px',
      md: uniq[1]?.raw || uniq[0]?.raw || '8px',
      lg: uniq[2]?.raw || uniq[1]?.raw || '12px',
      xl: uniq[3]?.raw || uniq[2]?.raw || '16px',
      pill: uniq.find((x) => x.n >= 999)?.raw || '9999px',
    };
  })();

  const largestByFont = (arr, tag) => arr.filter((x) => !tag || x.tag === tag).sort((a, b) => (pxNum(b.fontSize) || 0) - (pxNum(a.fontSize) || 0))[0] || null;
  const nearestByFont = (arr, target) => arr.slice().sort((a, b) => Math.abs((pxNum(a.fontSize) || target) - target) - Math.abs((pxNum(b.fontSize) || target) - target))[0] || null;

  const h1Sample = largestByFont(headings, 'h1') || largestByFont(headings) || topTypoCombos[0]?.style || null;
  const h2Sample = largestByFont(headings, 'h2') || headings.sort((a, b) => (pxNum(b.fontSize) || 0) - (pxNum(a.fontSize) || 0))[1] || topTypoCombos[1]?.style || null;
  const h3Sample = largestByFont(headings, 'h3') || headings.sort((a, b) => (pxNum(b.fontSize) || 0) - (pxNum(a.fontSize) || 0))[2] || topTypoCombos[2]?.style || null;
  const bodySample = nearestByFont(paragraphs, 16) || topTypoCombos.find((x) => {
    const n = pxNum(x.style.fontSize);
    return n >= 14 && n <= 18;
  })?.style || null;
  const labelSample = buttons[0] || nearestByFont(paragraphs, 14) || topTypoCombos.find((x) => (pxNum(x.style.fontSize) || 0) <= 14)?.style || null;
  const smallSample = nearestByFont(paragraphs, 12) || topTypoCombos.find((x) => (pxNum(x.style.fontSize) || 0) <= 12)?.style || null;

  const classifyTheme = () => {
    const bgLum = luminance(bodyBg);
    if (bgLum == null) return 'unknown';
    if (bgLum < 0.2) return 'dark';
    if (bgLum > 0.8) return 'light';
    return 'mixed';
  };

  const themeMode = classifyTheme();
  const bodyContrast = contrastRatio(bodyBg, bodyText);
  const accentContrastOnAccent = contrastRatio(guessAccent, '#FFFFFF');
  const accentContrastOnBg = contrastRatio(guessAccent, bodyBg);

  const containerWidths = topMaxWidths
    .map(([raw, count]) => ({ raw, count, n: pxNum(raw) }))
    .filter((x) => x.n && x.n > 0)
    .sort((a, b) => a.n - b.n);

  const breakpoints = {
    content: containerWidths.find((x) => x.n >= 600)?.raw || null,
    desktop: containerWidths.find((x) => x.n >= 960)?.raw || null,
    wide: containerWidths.find((x) => x.n >= 1200)?.raw || null,
  };

  const tokenRef = (path) => `{${path}}`;

  const yamlTypographyBlock = (name, sample, fallback) => {
    const src = sample || fallback || {};
    const lines = [
      `${name}:`,
      `    fontFamily: ${JSON.stringify(src.fontFamily || topFonts[0]?.[0] || 'Inter')}`,
      `    fontSize: ${src.fontSize || fallback?.fontSize || '1rem'}`,
      `    fontWeight: ${String(src.fontWeight || fallback?.fontWeight || '400')}`,
      `    lineHeight: ${src.lineHeight || fallback?.lineHeight || '1.5'}`,
    ];
    if (src.letterSpacing && src.letterSpacing !== 'normal') lines.push(`    letterSpacing: ${src.letterSpacing}`);
    return lines.join('\n');
  };

  const inferredName = (() => {
    const host = location.hostname.replace(/^www\./, '');
    const title = cleanText(document.title).split(/[\-|·•—]/)[0].trim();
    return title || host || 'Extracted Design';
  })();

  const inferredDescription = `Extracted draft design system from ${location.hostname}${location.pathname} (${themeMode} UI).`;

  const componentYamlParts = [];
  if (primaryButton) {
    componentYamlParts.push(`  button-primary:\n    backgroundColor: ${JSON.stringify(primaryButton.backgroundColor || guessAccent)}\n    textColor: ${JSON.stringify(primaryButton.color || '#FFFFFF')}\n    typography: ${JSON.stringify(tokenRef('typography.label-md'))}\n    rounded: ${JSON.stringify(tokenRef('rounded.md'))}\n    padding: ${JSON.stringify(primaryButton.padding || `${chooseSpacingScale.sm} ${chooseSpacingScale.lg}`)}`);
  }
  if (secondaryButton) {
    componentYamlParts.push(`  button-secondary:\n    backgroundColor: ${JSON.stringify(secondaryButton.backgroundColor || bodyBg)}\n    textColor: ${JSON.stringify(secondaryButton.color || bodyText)}\n    borderColor: ${JSON.stringify(secondaryButton.borderColor || guessBorder)}\n    rounded: ${JSON.stringify(tokenRef('rounded.md'))}\n    padding: ${JSON.stringify(secondaryButton.padding || `${chooseSpacingScale.sm} ${chooseSpacingScale.lg}`)}`);
  }
  if (cardSample) {
    componentYamlParts.push(`  card-default:\n    backgroundColor: ${JSON.stringify(cardSample.backgroundColor || guessSurface)}\n    textColor: ${JSON.stringify(cardSample.color || bodyText)}\n    rounded: ${JSON.stringify(tokenRef('rounded.lg'))}`);
  }
  if (inputSample) {
    componentYamlParts.push(`  input-default:\n    backgroundColor: ${JSON.stringify(inputSample.backgroundColor || bodyBg)}\n    textColor: ${JSON.stringify(inputSample.color || bodyText)}\n    borderColor: ${JSON.stringify(inputSample.borderColor || guessBorder)}\n    rounded: ${JSON.stringify(tokenRef('rounded.md'))}`);
  }
  if (navSample) {
    componentYamlParts.push(`  nav-default:\n    backgroundColor: ${JSON.stringify(navSample.backgroundColor || bodyBg)}\n    textColor: ${JSON.stringify(navSample.color || bodyText)}\n    rounded: ${JSON.stringify(tokenRef('rounded.md'))}`);
  }
  if (badgeSample) {
    componentYamlParts.push(`  badge-default:\n    backgroundColor: ${JSON.stringify(badgeSample.backgroundColor || guessMutedSurface)}\n    textColor: ${JSON.stringify(badgeSample.color || bodyText)}\n    rounded: ${JSON.stringify(tokenRef('rounded.pill'))}`);
  }

  const hoverCandidates = uniqueBy(
    [...document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]')]
      .slice(0, 30)
      .map((el) => {
        const s = getComputedStyle(el);
        return {
          tag: el.tagName.toLowerCase(),
          className: typeof el.className === 'string' ? el.className : '',
          text: trunc(el.textContent || el.value || ''),
          color: normColor(s.color),
          backgroundColor: normColor(s.backgroundColor),
          borderColor: normColor(s.borderColor),
          cursor: s.cursor,
          transition: s.transition,
        };
      }),
    (x) => `${x.tag}|${x.className}|${x.backgroundColor}|${x.color}`
  );

  const tokensJson = {
    meta: {
      name: inferredName,
      url: location.href,
      extractedAt: now,
      themeMode,
    },
    colors: {
      background: bodyBg,
      surface: guessSurface,
      'surface-muted': guessMutedSurface,
      primary: bodyText,
      secondary: guessSecondaryText,
      accent: guessAccent,
      border: guessBorder,
      'on-accent': '#FFFFFF',
    },
    typography: {
      h1: h1Sample,
      h2: h2Sample,
      h3: h3Sample,
      'body-md': bodySample,
      'label-md': labelSample,
      'body-sm': smallSample,
    },
    rounded: chooseRadiusScale,
    spacing: chooseSpacingScale,
    layout: {
      gap: topGaps.map(([raw, count]) => ({ raw, count })),
      maxWidth: topMaxWidths.map(([raw, count]) => ({ raw, count })),
      breakpoints,
    },
    components: {
      'button-primary': primaryButton,
      'button-secondary': secondaryButton,
      'card-default': cardSample,
      'input-default': inputSample,
      'nav-default': navSample,
      'badge-default': badgeSample,
    },
  };

  const findings = [];
  if (bodyContrast != null) {
    findings.push({
      severity: bodyContrast >= 4.5 ? 'info' : 'warning',
      path: 'colors.primary/background',
      message: `Body text contrast vs background: ${bodyContrast}:1`,
    });
  }
  if (accentContrastOnAccent != null) {
    findings.push({
      severity: accentContrastOnAccent >= 4.5 ? 'info' : 'warning',
      path: 'colors.accent/on-accent',
      message: `Accent with white text contrast: ${accentContrastOnAccent}:1`,
    });
  }
  if (accentContrastOnBg != null) {
    findings.push({
      severity: accentContrastOnBg >= 3 ? 'info' : 'warning',
      path: 'colors.accent/background',
      message: `Accent vs background contrast: ${accentContrastOnBg}:1`,
    });
  }
  if (distinctText.length > 8) {
    findings.push({
      severity: 'warning',
      path: 'colors.text',
      message: `Many distinct text colors detected (${distinctText.length} among top samples). Site may contain one-off exceptions or inconsistent token usage.`,
    });
  }
  if (topRadii.length > 6) {
    findings.push({
      severity: 'warning',
      path: 'rounded',
      message: `Many radius values detected (${topRadii.length} among top samples). Consider consolidating the shape scale manually.`,
    });
  }

  const designMd = `---
version: alpha
name: ${JSON.stringify(inferredName)}
description: ${JSON.stringify(inferredDescription)}
colors:
  background: ${JSON.stringify(bodyBg)}
  surface: ${JSON.stringify(guessSurface)}
  surface-muted: ${JSON.stringify(guessMutedSurface)}
  primary: ${JSON.stringify(bodyText)}
  secondary: ${JSON.stringify(guessSecondaryText)}
  accent: ${JSON.stringify(guessAccent)}
  border: ${JSON.stringify(guessBorder)}
  on-accent: "#FFFFFF"
typography:
  ${yamlTypographyBlock('h1', h1Sample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '3rem', fontWeight: '700', lineHeight: '1.1' })}
  ${yamlTypographyBlock('h2', h2Sample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '2rem', fontWeight: '600', lineHeight: '1.2' })}
  ${yamlTypographyBlock('h3', h3Sample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '1.5rem', fontWeight: '600', lineHeight: '1.25' })}
  ${yamlTypographyBlock('body-md', bodySample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '1rem', fontWeight: '400', lineHeight: '1.5' })}
  ${yamlTypographyBlock('body-sm', smallSample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '0.875rem', fontWeight: '400', lineHeight: '1.4' })}
  ${yamlTypographyBlock('label-md', labelSample, { fontFamily: topFonts[0]?.[0] || 'Inter', fontSize: '0.875rem', fontWeight: '500', lineHeight: '1.3' })}
rounded:
  sm: ${chooseRadiusScale.sm}
  md: ${chooseRadiusScale.md}
  lg: ${chooseRadiusScale.lg}
  xl: ${chooseRadiusScale.xl}
  pill: ${chooseRadiusScale.pill}
spacing:
  xs: ${chooseSpacingScale.xs}
  sm: ${chooseSpacingScale.sm}
  md: ${chooseSpacingScale.md}
  lg: ${chooseSpacingScale.lg}
  xl: ${chooseSpacingScale.xl}
  2xl: ${chooseSpacingScale['2xl']}
components:
${componentYamlParts.join('\n') || '  # No strong recurring components detected automatically'}
---

## Overview

This DESIGN.md was extracted from a live page and should be treated as a strong first-pass draft rather than a final source of truth.
The page reads as a **${themeMode}** interface with dominant colors and typography inferred from computed styles across visible elements.

## Colors

The palette was derived from the most common text, surface, border, and interactive colors.

- **Background (${bodyBg}):** main page canvas.
- **Surface (${guessSurface}):** cards, panels, or contained sections.
- **Primary (${bodyText}):** dominant readable text color.
- **Secondary (${guessSecondaryText}):** subdued supporting text.
- **Accent (${guessAccent}):** links, buttons, or interactive emphasis.
- **Border (${guessBorder}):** lines, dividers, and input outlines.

## Typography

Typography tokens were inferred from recurring heading, body, and UI-label styles found in computed values.
The dominant family appears to be ${JSON.stringify(topFonts[0]?.[0] || bodyStyle.fontFamily || 'unknown')}.

## Layout

Spacing tokens were inferred from repeated margin, padding, and gap values.
${breakpoints.content || breakpoints.desktop || breakpoints.wide ? `Likely content/container widths detected: ${[breakpoints.content, breakpoints.desktop, breakpoints.wide].filter(Boolean).join(', ')}.` : 'No strong max-width breakpoints were confidently inferred from the current viewport.'}

## Elevation & Depth

${topShadows.length ? `Visible shadows suggest layered surfaces or interaction states. The most common shadow pattern is ${JSON.stringify(topShadows[0][0])}.` : 'The UI appears mostly flat with minimal visible shadow layering.'}

## Shapes

Corner radius tokens were inferred from the most frequent rounded values across components.
The design leans on ${chooseRadiusScale.md}–${chooseRadiusScale.lg} as the probable default range.

## Components

Buttons, cards, inputs, navigation, and badge-like elements were sampled from visible recurring patterns where possible.
Component tokens may need manual cleanup if the source site mixes marketing, content, and application surfaces.

## Do's and Don'ts

- Do keep new UI aligned with the extracted spacing and radius scales.
- Do reuse the accent color for primary interaction emphasis.
- Do verify hover, focus, and mobile states manually before treating this as final.
- Don't preserve every one-off exception from the source site.
- Don't introduce extra colors until you verify whether they belong to the core system.
`;

  const consoleHelpers = {
    copyDesignMd: 'copy(window.__designExtractionV2.designMd)',
    copyJson: 'copy(JSON.stringify(window.__designExtractionV2, null, 2))',
    copyTokens: 'copy(JSON.stringify(window.__designExtractionV2.tokensJson, null, 2))',
  };

  const result = {
    meta: {
      url: location.href,
      title: document.title,
      extractedAt: now,
      totalElements: allEls.length,
      totalVisibleElements: visibleEls.length,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
        dpr: window.devicePixelRatio,
      },
      themeMode,
    },
    raw: {
      cssVars,
      body: {
        backgroundColor: normColor(bodyStyle.backgroundColor),
        color: normColor(bodyStyle.color),
        fontFamily: bodyStyle.fontFamily,
        fontSize: bodyStyle.fontSize,
        lineHeight: bodyStyle.lineHeight,
      },
      frequencies: {
        textColors: topTextColors,
        bgColors: topBgColors,
        borderColors: topBorderColors,
        fontFamilies: topFonts,
        fontSizes: topFontSizes,
        radii: topRadii,
        spacing: topSpacing,
        gaps: topGaps,
        shadows: topShadows,
        maxWidths: topMaxWidths,
        typographyCombos: topTypoCombos,
      },
      samples,
      interactiveCandidates: hoverCandidates,
    },
    analysis: {
      inferredName,
      inferredDescription,
      themeMode,
      contrast: {
        bodyTextOnBackground: bodyContrast,
        whiteOnAccent: accentContrastOnAccent,
        accentOnBackground: accentContrastOnBg,
      },
      breakpoints,
      findings,
    },
    draftTokens: tokensJson,
    tokensJson,
    designMd,
    consoleHelpers,
  };

  window.__designExtractionV2 = result;
  console.log('Extraction saved to window.__designExtractionV2');
  console.log('Copy helpers:', consoleHelpers);
  console.log(result);
  return result;
})();

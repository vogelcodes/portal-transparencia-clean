#!/usr/bin/env node
/**
 * CLI tool: Convert DESIGN.md to tailwind.theme.json
 *
 * Usage:
 *   node design-to-tailwind.js DESIGN.md > tailwind.theme.json
 *   node design-to-tailwind.js DESIGN.md -o tailwind.theme.json
 */

const fs = require("fs");
const path = require("path");

// Parse YAML front matter (simple parser for DESIGN.md format)
function parseDesignMd(content) {
  // Match YAML between opening --- and closing ---
  // Handle both with and without trailing newline
  const match = content.match(/^---\r?\n?([\s\S]*?)\r?\n?---/);
  if (!match) {
    throw new Error("Invalid DESIGN.md format: no YAML front matter found");
  }
  // Debug: uncomment to see raw YAML
  // console.error("RAW YAML:\n" + match[1].slice(0, 500));
  return parseYaml(match[1]);
}

// Simple YAML parser for our specific format
function parseYaml(yaml) {
  const result = {};
  const lines = yaml.split("\n");

  // Track the path: [section, key1, key2, ...]
  let path = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;

    const indent = line.match(/^(\s*)/)[1].length;
    const content = line.trim();

    // Calculate depth (0, 2, 4 spaces)
    const depth = Math.floor(indent / 2);

    if (content.endsWith(":") && !content.includes("{")) {
      // Section or key header
      const name = content.slice(0, -1);
      path = path.slice(0, depth);
      path.push(name);

      // Initialize nested structure
      let obj = result;
      for (let p = 0; p < path.length - 1; p++) {
        if (!obj[path[p]]) obj[path[p]] = {};
        obj = obj[path[p]];
      }
      if (!obj[name]) obj[name] = {};
    } else if (content.includes(":")) {
      // Key-value pair
      const colonIdx = content.indexOf(":");
      let key = content.slice(0, colonIdx).trim();
      let value = content.slice(colonIdx + 1).trim();

      // Remove quotes
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }

      // Navigate to correct depth
      path = path.slice(0, depth + 1);

      let obj = result;
      for (let p = 0; p < path.length; p++) {
        if (!obj[path[p]]) obj[path[p]] = {};
        obj = obj[path[p]];
      }
      obj[key] = value;
    }
  }

  return result;
}

// Convert to Tailwind theme format
function convertToTailwind(designTokens) {
  const theme = {
    colors: {},
    fontFamily: {},
    fontSize: {},
    borderRadius: {},
    spacing: {},
    boxShadow: {},
  };

  // Colors
  if (designTokens.colors) {
    const colors = designTokens.colors;
    theme.colors = { ...colors };

    // Add color aliases for common patterns
    if (colors.surface) theme.colors["surface-default"] = colors.surface;
    if (colors.primary) theme.colors["primary-default"] = colors.primary;
    if (colors.secondary) theme.colors["secondary-default"] = colors.secondary;
    if (colors.error) theme.colors["error-default"] = colors.error;
  }

  // Typography
  if (designTokens.typography) {
    for (const [name, props] of Object.entries(designTokens.typography)) {
      if (typeof props === "object" && props.fontFamily) {
        // Extract font size value
        const fontSize = props.fontSize || "16px";
        const fontWeight = props.fontWeight || "400";
        const lineHeight = props.lineHeight || "1.5";
        const letterSpacing = props.letterSpacing;

        const themeObj = {
          lineHeight,
        };
        if (fontWeight) themeObj.fontWeight = fontWeight;
        if (letterSpacing) themeObj.letterSpacing = letterSpacing;

        theme.fontSize[name] = [fontSize, themeObj];

        // Add font family if not already present
        const fontFamily = props.fontFamily
          .replace(/"/g, "")
          .split(",")[0]
          .trim();
        if (!theme.fontFamily[fontFamily.toLowerCase()]) {
          theme.fontFamily[fontFamily.toLowerCase()] = props.fontFamily;
        }
      }
    }
  }

  // Rounded
  if (designTokens.rounded) {
    theme.borderRadius = { ...designTokens.rounded };
  }

  // Spacing
  if (designTokens.spacing) {
    theme.spacing = {
      unit: "8px",
      container: "24px",
      card: "16px",
      section: "40px",
      ...designTokens.spacing,
    };
  }

  // Box shadows (inferred from components or added as defaults)
  theme.boxShadow = {
    card: "0 6px 6px rgba(0, 0, 0, 0.16)",
    elevated: "0 8px 16px rgba(0, 0, 0, 0.2)",
    glass: "0 8px 32px 0 rgba(0, 0, 0, 0.1)",
  };

  return theme;
}

// Main
function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error(
      "Usage: node design-to-tailwind.js <DESIGN.md> [-o <output>]",
    );
    process.exit(1);
  }

  let inputFile = null;
  let outputFile = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "-o" || args[i] === "--output") {
      outputFile = args[++i];
    } else if (!inputFile) {
      inputFile = args[i];
    }
  }

  if (!inputFile) {
    console.error("Error: No input file specified");
    process.exit(1);
  }

  try {
    const content = fs.readFileSync(inputFile, "utf8");
    const designTokens = parseDesignMd(content);
    const tailwindTheme = convertToTailwind(designTokens);
    const json = JSON.stringify(tailwindTheme, null, 2);

    if (outputFile) {
      fs.writeFileSync(outputFile, json);
      console.log(`✓ Written to ${outputFile}`);
    } else {
      console.log(json);
    }
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();

// Webview check: run the app's own LaTeX-to-HTML renderer (frontend/src/components/
// browser/LatexContent.tsx, KaTeX 0.17 with the app's options) on each input file
// and fail on anything that would render wrong in the app's web view.
//
// Usage: node check_web.mjs <file1.tex> [file2.tex ...]
// Prints a JSON array of {file, ok, errors}.
//
// The renderer is bundled from the frontend source with esbuild on first use (and
// again whenever the source changes), so this check always tracks the real app.

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..", "..");
const frontend = path.join(repo, "frontend");
const srcDir = path.join(frontend, "src", "components", "browser");
const src = path.join(srcDir, "LatexContent.tsx");
const srcDeps = [src, path.join(srcDir, "latexWebSanitize.ts")];
const bundle = path.join(here, "_render_bundle.mjs");
const require = createRequire(path.join(frontend, "package.json"));

async function ensureBundle() {
  const newest = Math.max(...srcDeps.filter(fs.existsSync).map((f) => fs.statSync(f).mtimeMs));
  const stale = !fs.existsSync(bundle) || fs.statSync(bundle).mtimeMs < newest;
  if (!stale) return;
  const esbuild = require("esbuild");
  await esbuild.build({
    entryPoints: [src],
    bundle: true,
    platform: "node",
    format: "esm",
    outfile: bundle,
    absWorkingDir: frontend,
    logLevel: "silent",
    jsx: "automatic",
    plugins: [
      {
        name: "amplify-stubs",
        setup(b) {
          b.onResolve({ filter: /\.css$/ }, (a) => ({ path: a.path, namespace: "amp-empty" }));
          b.onLoad({ filter: /.*/, namespace: "amp-empty" }, () => ({ contents: "", loader: "js" }));
          b.onResolve({ filter: /lib\/ipc$/ }, (a) => ({ path: a.path, namespace: "amp-ipc" }));
          b.onLoad({ filter: /.*/, namespace: "amp-ipc" }, () => ({
            contents: "export const ipc = { resolve_images: async () => ({}) };",
            loader: "js",
          }));
        },
      },
    ],
  });
}

function decodeEntities(s) {
  return s
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

// Remove every <span class="katex ..."> ... </span> block (nested spans inside)
// so that whatever text is left is prose the app would show as-is.
function stripKatexBlocks(html) {
  let out = "";
  let i = 0;
  const openRe = /<span class="katex(?:-display)?"/g;
  while (i < html.length) {
    openRe.lastIndex = i;
    const m = openRe.exec(html);
    if (!m) {
      out += html.slice(i);
      break;
    }
    out += html.slice(i, m.index);
    // walk span tags to find the matching close
    let depth = 0;
    let j = m.index;
    const tagRe = /<\/?span\b[^>]*>/g;
    tagRe.lastIndex = j;
    let t;
    let end = html.length;
    while ((t = tagRe.exec(html)) !== null) {
      if (t[0].startsWith("</")) depth -= 1;
      else if (!t[0].endsWith("/>")) depth += 1;
      if (depth === 0) {
        end = t.index + t[0].length;
        break;
      }
    }
    out += " ";
    i = end;
  }
  return out;
}

function analyze(source, html) {
  const errors = [];
  const errRe = /<span class="katex-error"[^>]*title="([^"]*)"/g;
  let m;
  while ((m = errRe.exec(html)) !== null) {
    errors.push("KaTeX: " + decodeEntities(m[1]).slice(0, 300));
  }
  let rest = html.replace(/<span class="katex-error"[^>]*>[\s\S]*?<\/span>/g, " ");
  rest = stripKatexBlocks(rest);
  rest = rest.replace(/<[^>]+>/g, " ");
  rest = decodeEntities(rest);
  const leftovers = new Set();
  for (const mm of rest.matchAll(/\\(begin|end)\{[^}]*\}|\\[A-Za-z@]+|\\\\/g)) {
    leftovers.add(mm[0]);
  }
  if (leftovers.size) {
    errors.push(
      "raw LaTeX would show as text in the web view: " + [...leftovers].slice(0, 12).join(" "),
    );
  }
  if (/[{}]/.test(rest)) {
    errors.push("stray brace would show as text in the web view");
  }
  if (/@@AMP_/.test(html)) {
    errors.push("renderer sentinel leaked into output");
  }
  const unmatched = /<code>[\s\S]*?<\/code>/.test(html) && !/\\texttt/.test(source);
  if (unmatched) {
    errors.push("KaTeX threw on an expression (rendered as code fallback)");
  }
  return errors;
}

async function main() {
  const files = process.argv.slice(2);
  await ensureBundle();
  const mod = await import(pathToFileURL(bundle).href);
  const renderLatex = mod.renderLatex;
  if (typeof renderLatex !== "function") {
    console.error("renderLatex export not found in bundle");
    process.exit(2);
  }
  const results = [];
  for (const f of files) {
    const source = fs.readFileSync(f, "utf8").replace(/\r\n/g, "\n");
    try {
      const html = renderLatex(source);
      const errors = analyze(source, html);
      results.push({ file: f, ok: errors.length === 0, errors });
    } catch (e) {
      results.push({ file: f, ok: false, errors: ["renderer threw: " + String(e).slice(0, 300)] });
    }
  }
  process.stdout.write(JSON.stringify(results));
}

main().catch((e) => {
  console.error(String(e));
  process.exit(2);
});

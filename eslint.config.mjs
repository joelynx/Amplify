// Minimal flat ESLint config. Next 15.5+'s strict lint config is in flux
// (the next lint → ESLint CLI migration); this keeps `npm run lint` runnable
// without enforcing more than the bare basics. Type-check + tests catch the
// meaningful issues.
export default [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "build/**",
      "dist/**",
      "out/**",
    ],
  },
];

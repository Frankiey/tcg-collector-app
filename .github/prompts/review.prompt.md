---
description: "Use when reviewing code changes to the app. Applies project-specific review criteria."
---

# Code Review Prompt

Review with these project-specific criteria:

## Must check
- [ ] No build step introduced (no npm, webpack, vite, etc.)
- [ ] No ES module `import`/`export` statements added
- [ ] `pokemonData.js` not edited by hand
- [ ] Offline fallback chain preserved (IndexedDB → localStorage → pokemonData.js)
- [ ] CSS uses variables from `:root`, no hardcoded colors
- [ ] `v-once` used on static content in Vue templates
- [ ] No Vuex/Pinia — state stays on root Vue instance

## If API code changed
- [ ] API calls go through `CONFIG` base URL
- [ ] Response mapping is separate from rendering
- [ ] Changes align with current migration phase (check `MIGRATION.md`)
- [ ] Backward compatibility with cached IndexedDB data considered

## If styles changed
- [ ] CSS variables used (not hardcoded values)
- [ ] Added to correct section in `styles.css`
- [ ] Responsive behavior maintained
- [ ] Glassmorphism aesthetic preserved

## If cached assets changed
- [ ] `CACHE_NAME` version bumped in `sw.js`

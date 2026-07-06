---
name: FuckFortySeven
description: Negative DJT news rendered as muted pop-art posters with punk-flyer typography
colors:
  xerox-black: "#221f1a"
  newsprint-gray: "#dfe2dd"
  flyer-stock: "#f1e6c9"
  jagger-tan: "#e8b98a"
  slate-plate: "#48566d"
  orchid-plate: "#ce769e"
typography:
  masthead:
    fontFamily: "Anton, Arial Narrow, Impact, sans-serif"
    fontSize: "clamp(1.5625rem, 3.125vw, 2.1875rem)"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.02em"
  tagline:
    fontFamily: "Special Elite, Courier New, monospace"
    fontSize: "clamp(1.25rem, 2.5vw, 1.75rem)"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Anton, Arial Narrow, Impact, sans-serif"
    fontSize: "clamp(3.51rem, 7.8vw + 0.78rem, 8.19rem)"
    fontWeight: 400
    lineHeight: 1.28
    letterSpacing: "0.005em"
  body:
    fontFamily: "Special Elite, Courier New, monospace"
    fontSize: "1.56rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Special Elite, Courier New, monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.08em"
components:
  button-control:
    backgroundColor: "{colors.xerox-black}"
    textColor: "{colors.newsprint-gray}"
    typography: "{typography.masthead}"
    padding: "10px 22px"
    height: "44px"
  button-control-hover:
    backgroundColor: "{colors.slate-plate}"
    textColor: "{colors.newsprint-gray}"
  card-story:
    backgroundColor: "{colors.flyer-stock}"
    textColor: "{colors.xerox-black}"
    padding: "16px 20px"
  headline-strip:
    backgroundColor: "{colors.xerox-black}"
    textColor: "#ffffff"
    typography: "{typography.headline}"
    padding: "0.09em 0.18em"
  stamp:
    backgroundColor: "{colors.orchid-plate}"
    textColor: "{colors.xerox-black}"
    typography: "{typography.label}"
    padding: "6px 10px"
---

# Design System: FuckFortySeven

## 1. Overview

**Creative North Star: "The Garage Print Run"**

Every screen is a print artifact, not a web page: a silkscreen poster pulled in someone's garage, or a gig flyer xeroxed at 2am and stapled to a phone pole. Two lineages own two layers and never blend. The **image layer** is muted Warhol/Lichtenstein — a high-contrast black photographic plate over flat, slightly off-register blocks of muted color, halftone texture where the print metaphor earns it. The **type layer** is Raymond Pettibon's Black Flag flyers — dense ultra-condensed heavy caps, cramped typewriter paste-up text, everything set in xerox black. The collision of the two layers IS the identity.

This system explicitly rejects: generic SaaS/AI template moves (gradients, card grids, glassmorphism), the visual credibility of real news outlets (NYT/CNN/BBC), low-effort meme-site sloppiness, and theme-park pop art (full-saturation Lichtenstein primaries, "POW!" clichés, Warhol grids-of-four). The roughness is a crafted print aesthetic executed with production precision.

Motion is **restrained**: poster rotation is a hard cut, like flipping through a stack of flyers. No easing choreography, no orchestrated entrances. State changes happen instantly or not at all; `prefers-reduced-motion` is trivially satisfied because almost nothing moves.

**Key Characteristics:**

- One full-viewport poster per article; portrait dominates the right half, type stacks in the left half
- Misregistered muted color plates under a duotone-treated portrait, printed through an SVG silkscreen filter and dot-halftone overlay
- Anton condensed caps on paste-up ink strips + Special Elite typewriter body copy on a flyer-stock card
- Flat, printed, paper-honest; zero digital-native effects
- Hard cuts between posters via Alpine index rotation; motion by exception only

## 2. Colors: The Print-Shop Palette

Six plates and paper stocks, all inked into `:root` custom properties on `app/index.html`. Values are anchors sampled from aged print reproductions — never drift toward full-saturation primaries. All values are canonical hex sRGB; there is no OKLCH source of truth.

### Primary

- **Xerox Black** (`--ink`, `#221f1a`): The black plate. Carries the duotone photographic silkscreen layer, all typography, buttons, and geometry. Warm and inky, never `#000` — pure black reads digital, this reads printed.

### Secondary

- **Jagger Tan** (`--tan`, `#e8b98a`): The flesh-tone block plate sitting under the portrait, deliberately off-register by 12px down and left. Never used behind text.
- **Slate Plate** (`--olive`, `#48566d`): The second block plate — a muted slate blue-gray held under the story card and used as the hover state for the black button plates. The CSS variable is legacy-named `--olive` (the reference Warhol Jagger palette used olive-gold there); the actual value swaps in slate so the tan plate carries the warm register alone.

### Tertiary

- **Orchid Plate** (`--orchid`, `#ce769e`): The single loud accent, used the way Warhol used pink on Jagger's lips and eyes: one or two small, decisive strokes per poster. Currently spent on the rotated **issue stamp** ("No. 3 of 29") and the byline link hover.

### Neutral

- **Newsprint Gray** (`--ground`, `#dfe2dd`): Default page surface — a cool off-white with a hint of blue-gray. This is the paper stock the whole poster prints onto and the color that ink-buttons use for their text.
- **Flyer Stock** (`--stock`, `#f1e6c9`): Aged flyer paper, the paper-toned plate that sits behind the description card so typewriter body copy reads clearly over portrait imagery.

### Named Rules

**The Off-Register Rule.** Color plates never align perfectly with the black plate. The Jagger Tan plate under the portrait is transformed `translate(-12px, 12px)` from the photo above it; the Slate Plate under the story card overhangs by 28px on each side. Pixel-perfect alignment reads digital and is forbidden.

**The One Pink Rule.** Orchid Plate appears at most twice per poster and always in small areas — the rotated issue stamp is one; the byline `.byline a:hover { background: var(--orchid) }` is the other. If pink covers more than ~5% of the viewport, it has stopped being a Warhol accent and started being a theme.

## 3. Typography

**Display Font:** Anton (with Arial Narrow, Impact, sans-serif) — ultra-condensed heavy grotesque; self-hosted `app/fonts/anton.woff2`. Used for the masthead site name, the article headline, and every action button (prev/next/back-issues/read-the-story).

**Body Font:** Special Elite (with Courier New, monospace) — typewriter slab with battered impact character; self-hosted `app/fonts/special-elite.woff2`. Used for the tagline, description, byline, and marginalia. All body text lives on the Flyer Stock card so typewriter roughness doesn't fight portrait halftone.

**Character:** Anton sits like a masthead barely fitting the paper — letters shoulder into each other, minimal tracking. Special Elite reads like paste-up typewriter columns glued down on the flyer. The contrast axis is condensed-grotesque vs. mechanical-slab; both are unmistakably print. No fallback font in the stack is a serif — the serif register would break the punk-flyer voice.

### Hierarchy

- **Masthead** (Anton 400, `clamp(1.5625rem, 3.125vw, 2.1875rem)`, uppercase, tracking `0.02em`): The site title "Fuck Forty Seven" at the top-left of the type column. Bumped +25% over its base at desktop widths (≥900px).
- **Tagline** (Special Elite 400, `clamp(1.25rem, 2.5vw, 1.75rem)`, `line-height: 1.5`): "all bad news, all the time" directly below the masthead. Same clamp slope as the masthead so both scale together with viewport width.
- **Headline** (Anton 400, `clamp(3.51rem, 7.8vw + 0.78rem, 8.19rem)`, `line-height: 1.28`, uppercase, tracking `0.005em`, `text-wrap: balance`): The article title, JS-fit between `MIN_PX = 56.4px` and `MAX_PX = 132px` on desktop to fill the available column height, with a wrap-line-count cap that prevents short titles from stacking into narrow columns. Two shorter variants (`[data-len="long"]`, `[data-len="xlong"]`) step the clamp down for long titles. Text sits inside inline paste-up ink strips (`h1.headline span { background: var(--ink); box-decoration-break: clone; padding: 0.09em 0.18em }`) so each wrapped line gets its own paper-cut edge in Xerox Black.
- **Body** (Special Elite 400, `1rem` mobile / `1.56rem` desktop, `line-height: 1.5`, max ~54ch): The `.desc` paragraph inside the story card. On desktop the JS auto-fit tries `[24.96, 21.6, 19.2, 17.4]px` and picks the largest size that still leaves headroom for the headline to be ≥1.2× the body.
- **Label** (Special Elite 400, `0.8125rem`, uppercase, tracking `0.08em`): The `.byline` row (source · date · Read the story), the issue stamp, and the credit gutter. Flyer marginalia energy — "$7.00 · DOORS AT 7PM" cadence.

### Named Rules

**The Masthead Rule.** One headline per poster, and it is enormous. Nothing else on the page competes with it typographically — no second heading, no pull quote, no eyebrow labels above sections.

**The Paste-Up Rule.** Headline text always sits inside `background: var(--ink)` inline strips with `box-decoration-break: clone`, one strip per wrapped line. Never as reverse-out black type on paper; always as ink strips over paper. This is what makes the punk flyer read as pasted, not typeset.

## 4. Elevation

None. This is ink on paper: no `box-shadow`, no `filter: blur()` on decorative surfaces, no `backdrop-filter`, no gradients anywhere. Depth is conveyed exclusively by print artifacts — plate misregistration (The Off-Register Rule), overlapping color blocks between the `.plate-tan` / `.plate-olive` / `.portrait-frame` layers, a 5×5 dot halftone overlay (`radial-gradient(circle, rgba(34,31,26,0.32) 1px, transparent 1.4px)`), and paper-toned Flyer Stock plates placed behind text.

A semantic z-scale (`--z-plate: 1` → `--z-portrait: 2` → `--z-halftone: 3` → `--z-type: 4` → `--z-controls: 5`) enforces stacking order without magic numbers. Focus states use a hard `3px solid var(--ink)` outline with `outline-offset: 2px` — a printed rule, not a glow.

### Named Rules

**The Flat Ink Rule.** `box-shadow`, decorative `filter: blur()`, `backdrop-filter`, and gradients are prohibited. The only permitted "effects" are print processes: the SVG `#silkscreen` filter that duotones the portrait (feColorMatrix saturate 0 → feComponentTransfer contrast push → posterize to 5 levels), the CSS dot-halftone overlay on `.halftone`, and the deliberate `translate()` off-registers on `.plate-tan` and `.plate-olive`.

## 5. Components

Every component below ships in `app/index.html` and is used by the single-poster page. Coordinates and paddings are the actual production values.

### Poster shell (`.poster`, `.portrait-frame`, `.plate-tan`, `.plate-olive`, `.halftone`)

- **Shape:** Full-viewport (`100vw × 100dvh`), `overflow: hidden`. Split into a right-half portrait pane (`width: 50vw`) and a left-half type column below.
- **Layers, bottom-up (z-scale):** `.plate-tan` (Jagger Tan block, `translate(-12px, 12px)` behind the portrait) → `.plate-olive` (Slate Plate band under the story card, positioned by the `.story`'s own geometry so it overhangs 28px on each side) → `.portrait-frame img` with `filter: url(#silkscreen)` (duotone posterize) → `.halftone` (5×5 dot grid overlay at 32% ink opacity) → `.type-col` (the type layer) → `.controls` / `.stamp` (interactive top).
- **Behavior:** Instant swap when Alpine rotates `idx`. No transition on portrait change — this is the flyer-stack hard cut.
- **Mobile (< 900px):** Portrait becomes a top band (`height: 58dvh`), Slate Plate is `display: none`, type flows below in a static column.

### Masthead (`.masthead`, `.masthead .site`, `.masthead .tagline`)

- **Position:** Top-left of the type column, `padding-top: clamp(16px, 3vh, 32px)`, `padding-left: clamp(16px, 3vw, 48px)`.
- **Composition:** Anton "FUCK FORTY SEVEN" masthead over Special Elite "all bad news, all the time" tagline. Both scale with the same `2.5vw` slope on desktop so their size ratio stays constant across viewport widths.
- **Behavior:** The site name is a link back to `/`; the tagline is plain text. No hover state on the masthead itself.

### Headline block (`.headline-block`, `h1.headline`, `h1.headline span`)

- **Shape:** Fits the type column's content box (`content-group` has `align-self: stretch`, `align-items: center`); headline block max-width capped by `min(46vw, 66ch, 100%)` so it can't overflow at half-widths on ultrawide monitors.
- **Content:** One `<h1>` with a `<span>` inside `x-text="current.title"`. Every wrapped line gets its own Xerox Black paste-up strip via `background: var(--ink); box-decoration-break: clone`.
- **JS-fit behavior:** On desktop `fitHeadline()` binary-searches font size in `[56.4px, 132px]` to fill the vertical space between masthead and story card, then reduces further if the resulting wrap-line count exceeds `Math.max(2, floor(titleLen / 16))` — prevents short titles from stacking into narrow columns.

### Story card (`.story`, `.story .desc`, `.story .byline`)

- **Shape:** `width: min(35vw, 54ch)` on desktop, `background: var(--stock)` Flyer Stock paper, `padding: 16px 20px`. Sits centered inside the content-group with 25–36px indent on either side (the visible story-plate overhang).
- **Slate Plate frame (desktop only):** Two pseudo-elements: `.story::before` — Slate Plate `#48566d` extending `24-30px` above, `18px` below, `28px` on each side; `.story::after` — Flyer Stock repaint on top so the description sits on paper not paint. The naked slate rim reads as the paper's own colored border.
- **Description:** Special Elite body text (`1.56rem` desktop, auto-fit down to `1.0875rem` if the headline needs more room).
- **Byline row:** Label-cased source · date · "Read the story" link. Link hover: `background: var(--orchid)` — the second permitted orchid stroke. Focus-visible: `outline: 3px solid var(--ink); outline-offset: 2px`.

### Buttons (`.controls button`, `.backissues a`) — Ink Plates

- **Shape:** Zero border-radius. Ink-black rectangle, Newsprint Gray text.
- **Typography:** Anton uppercase, `clamp(1.25rem, 2vw, 1.75rem)` (controls), `clamp(1.125rem, 4.5vw, 1.75rem)` (back-issues on mobile), letter-spacing `0.02em`.
- **Padding:** `10px 22px`, `min-height: 44px` (touch target).
- **States:**
  - Default: `background: var(--ink)`, `color: var(--ground)`.
  - Hover: `background: var(--slate-plate)`; no color shift on text.
  - Active (controls only): `transform: translate(1px, 1px)` — the physical press of a chunky stamp.
  - Focus-visible: `outline: 3px solid var(--ink); outline-offset: 2px`.
- **Placement:** `.controls` (prev / next) fixed to the bottom-right image edge on desktop; back-issues sits absolute at the bottom-left of the type column. On mobile, `.controls` is `position: fixed` in the thumb zone (bottom-right), back-issues stacks into flow.

### Issue stamp (`.stamp`) — Orchid rotated ticket

- **Shape:** Orchid Plate rectangle with `transform: rotate(2deg)`, top-right of the poster.
- **Content:** `x-text="'No. ' + (idx + 1) + ' of ' + articles.length"`.
- **Typography:** Label size (`0.8125rem`), uppercase, tracking `0.08em`.
- **Padding:** `6px 10px`. Deliberately un-hoverable — this is a printed stamp, not a control.

### Credit gutter (`.credit`) — Vertical marginalia

- **Position:** Right edge of the poster, vertically centered, `writing-mode: vertical-rl`.
- **Content:** `x-text="'portrait: ' + image.credit"`.
- **Typography:** `0.6875rem` Special Elite at `opacity: 0.75`. Present at desktop only (`.credit { display: none }` on mobile).

### Poster rotation controller (Alpine `poster` data)

- **Signature component.** Not visible chrome, but the identity move. `Alpine.data('poster', { idx, images, articles, ... })` swaps portrait + article on every prev/next click and keeps the URL hash in sync with the article slug. Hash-driven deep links (e.g. `#tv-coverage-of-the-fourth-of-july-will-emphasize-holiday`) navigate the visitor directly to that article; unknown slugs fall back to `idx=0`. Rotation is instant — no crossfade, no transform-slide — because the visual language is a physical stack of flyers being turned over.

## 6. Do's and Don'ts

### Do

- **Do** compose each article as one full-viewport poster: duotone-treated DJT portrait on the right half, headline in Anton condensed caps on paste-up ink strips, small Special Elite description card on the left.
- **Do** misregister the tan and slate color plates under the black plate by the shipped offsets (`translate(-12px, 12px)` on `.plate-tan`, 28px story overhang on `.plate-olive`).
- **Do** treat portraits with the `url(#silkscreen)` SVG filter plus the 5×5 dot halftone overlay — both are print processes, not effects.
- **Do** place the Flyer Stock plate behind every block of body text; typewriter body copy never sits directly on portrait imagery.
- **Do** cut hard between posters. Alpine `idx` swap. No transitions on portrait change.
- **Do** scale the masthead site name and tagline together — same `2.5vw` clamp slope keeps them proportional.
- **Do** anchor the article content-group `clamp(24px, 4.5vh, 80px)` below the masthead so the gap stays constant on tall/portrait viewports instead of ballooning via auto-margin centering.
- **Do** use exactly two Orchid strokes per poster: the rotated issue stamp and the byline link hover — nothing else.

### Don't

- **Don't** use gradients, glassmorphism, card grids, or hero-metric layouts — the "generic SaaS/AI slop" named in PRODUCT.md.
- **Don't** imitate real news outlets (NYT, CNN, BBC) in typography, layout, or color; visual credibility undercuts the parody.
- **Don't** ship low-effort meme-site sloppiness; every rough edge must be a deliberate print artifact.
- **Don't** do theme-park pop art: no full-saturation red/yellow/blue Lichtenstein pastiche, no comic "POW!" bursts, no Warhol grid-of-four.
- **Don't** use pure `#000` or `#fff` anywhere; ink is Xerox Black (`#221f1a`), paper is Newsprint Gray (`#dfe2dd`).
- **Don't** add shadows, glows, or blurs (The Flat Ink Rule). Focus states are hard 3px ink outlines, not glows.
- **Don't** let Orchid Plate exceed two small strokes per poster (The One Pink Rule).
- **Don't** center-align the article headline text — headlines are left-aligned inside the paste-up strips so line ragging carries the hand-composed feel. Center-align breaks the flyer voice.
- **Don't** animate the portrait rotation. No crossfade, no slide, no scale. The stack-of-flyers metaphor is a hard cut.
- **Don't** add right-arrow glyphs to the ink-plate buttons. "Back issues", "Prev", "Next" ride on typography alone — the arrows that live on `Prev` / `Next` are HTML entities (`&larr;` / `&rarr;`) baked into the button label, not decorative additions.

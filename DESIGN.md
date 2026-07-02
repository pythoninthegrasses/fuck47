<!-- SEED: re-run /impeccable document once there's code to capture the actual tokens and components. -->
---
name: FuckFortySeven
description: Negative DJT news rendered as muted pop-art posters with punk-flyer typography
colors:
  xerox-black: "#221f1a"
  silkscreen-ground: "#f4efe3"
  flyer-stock: "#efddb7"
  jagger-tan: "#e8b98a"
  olive-plate: "#8a7749"
  orchid-plate: "#ce769e"
  flyer-orange: "#e59a2b"
  plum-ink: "#392229"
---

# Design System: FuckFortySeven

## 1. Overview

**Creative North Star: "The Garage Print Run"**

Every screen is a print artifact, not a web page: a silkscreen poster pulled in someone's garage, or a gig flyer xeroxed at 2am and stapled to a phone pole. Two lineages own two layers and never blend. The **image layer** is muted Warhol/Lichtenstein — a high-contrast black photographic plate over flat, slightly off-register blocks of muted color, halftone texture where the print metaphor earns it. The **type layer** is Raymond Pettibon's Black Flag flyers — dense ultra-condensed heavy caps, cramped typewriter paste-up text, everything set in xerox black. The collision of the two layers IS the identity.

This system explicitly rejects: generic SaaS/AI template moves (gradients, card grids, glassmorphism), the visual credibility of real news outlets (NYT/CNN/BBC), low-effort meme-site sloppiness, and theme-park pop art (full-saturation Lichtenstein primaries, "POW!" clichés, Warhol grids-of-four). The roughness is a crafted print aesthetic executed with production precision.

Motion is **restrained**: poster rotation is a hard cut, like flipping through a stack of flyers. No easing choreography, no orchestrated entrances. State changes happen instantly or not at all; `prefers-reduced-motion` is trivially satisfied because almost nothing moves.

**Key Characteristics:**
- One full-viewport poster per article; image dominates, headline detonates
- Misregistered muted color plates under a black photo plate
- Xerox-black condensed caps + typewriter subordinate text
- Flat, printed, paper-honest; zero digital-native effects
- Hard cuts between posters; motion by exception only

## 2. Colors: The Print-Shop Palette

Seven plates and two paper stocks, all sampled directly from the reference artifacts (the Warhol Jagger print and original Black Flag flyers in `~/Desktop/fuck47/`). Values are anchors sampled from aged print reproductions — tune within a hair's breadth during implementation, but stay muted; never drift toward full-saturation primaries.

### Primary
- **Xerox Black** (#221f1a): The black plate. Carries the photographic silkscreen layer, all typography, and the Black Flag-style geometry. It is warm and inky, never #000 — pure black reads digital, this reads printed.

### Secondary
- **Jagger Tan** (#e8b98a): The flesh-tone block plate. Sits under and around the portrait, deliberately off-register from the black plate above it.
- **Olive Plate** (#8a7749): The second block plate — muted olive-gold, used as a large misregistered field or garment block. Never as text.

### Tertiary
- **Orchid Plate** (#ce769e): The single loud accent, used the way Warhol used pink on Jagger's lips and eyes: one or two small, decisive strokes per poster. Rarity is the point.
- **Flyer Orange** (#e59a2b): Alternate paper stock for special treatments (the orange Black Flag flyer). When used, it is the whole surface, printed in **Plum Ink** (#392229) instead of Xerox Black.

### Neutral
- **Silkscreen Ground** (#f4efe3): Default page surface — the Warhol print's off-white ground. This is a pigment sampled from a specific artifact, not a decorative warm-neutral default.
- **Flyer Stock** (#efddb7): Aged flyer paper, for archive/secondary surfaces and paper-toned plates behind text.

### Named Rules
**The Off-Register Rule.** Color plates never align perfectly with the black plate. A 4–12px deliberate offset between a color block and the image/type it sits under is the signature move; pixel-perfect alignment reads digital and is forbidden on poster imagery.

**The One Pink Rule.** Orchid Plate appears at most twice per poster, in small areas. If pink covers more than ~5% of the viewport, it has stopped being a Warhol accent and started being a theme.

## 3. Typography

**Display Font:** [to be chosen at implementation — ultra-condensed heavy grotesque caps; the physical object is the "BLACK FLAG" masthead on a 1981 xeroxed gig flyer]
**Body Font:** [to be chosen at implementation — typewriter/monospaced slab; the physical object is typewritten paste-up columns crammed onto a flyer]

**Character:** Headline type is dense, black, and vertical — letters shoulder into each other like a masthead that barely fits the paper. Body type is small, mechanical, and cramped, like it was typed on a ribbon typewriter and glued down. The pairing contrasts on the condensed-vs-mechanical axis; both are unmistakably print.

All type is text-based ("fonts only" — no hand-lettered SVG headlines). Hand-drawn character comes from the fonts' own roughness and from layout (rotation, cramming, paste-up blocks), not from rendering text as artwork. Font selection at implementation time must follow the register's selection procedure and must not land on the reflex-reject list.

### Hierarchy
- **Display / Headline** (heavy, clamp to viewport, tight line-height ~0.9–1.0): the article headline; the loudest element on the poster after the image. All caps.
- **Body / Description** (small, ~0.8–0.9rem, line-height ~1.4): the article description beneath the headline. Subordinate by a wide margin; max 65ch.
- **Label** (small caps or typewriter, sparse): source attribution, dates, archive links. Flyer marginalia energy ("$7.00", "DOORS AT 7PM").

### Named Rules
**The Masthead Rule.** One headline per poster, and it is enormous. Nothing else on the page competes with it typographically — no second heading, no pull quote, no eyebrow labels.

## 4. Elevation

None. This is ink on paper: no box-shadows, no blurs, no layering metaphors from digital UI. Depth is conveyed exclusively by print artifacts — plate misregistration (The Off-Register Rule), overlapping color blocks, halftone density, and paper-toned plates placed behind text for legibility. If a surface needs separation, it gets a printed block of Flyer Stock or a hard 2px Xerox Black rule, never a shadow.

### Named Rules
**The Flat Ink Rule.** `box-shadow`, `filter: blur()` (decorative), `backdrop-filter`, and gradients are prohibited. Halftone, posterization, and duotone filters on imagery are the only permitted "effects" because they are print processes.

## 5. Components

Omitted — no components exist yet. This section lands on the next scan-mode run, once the poster page is built.

## 6. Do's and Don'ts

### Do:
- **Do** compose each article as one full-viewport poster: treated DJT image dominant, headline in condensed caps, small typewriter description.
- **Do** misregister color plates under the black plate by a visible 4–12px (The Off-Register Rule).
- **Do** use halftone/posterize/duotone treatments on portraits — in CSS/SVG or at build time; this is a static GitHub Pages site.
- **Do** place a paper-toned plate (Silkscreen Ground or Flyer Stock) behind any text that would otherwise sit on busy imagery; legibility outranks the aesthetic.
- **Do** cut hard between posters. Instant swaps, flyer-stack energy.

### Don't:
- **Don't** use gradients, glassmorphism, card grids, or hero-metric layouts — the "generic SaaS/AI slop" named in PRODUCT.md.
- **Don't** imitate real news outlets (NYT, CNN, BBC) in typography, layout, or color; visual credibility undercuts the parody.
- **Don't** ship low-effort meme-site sloppiness; every rough edge must be a deliberate print artifact.
- **Don't** do theme-park pop art: no full-saturation red/yellow/blue Lichtenstein pastiche, no comic "POW!" bursts, no Warhol grid-of-four.
- **Don't** use pure #000 or #fff anywhere; ink is Xerox Black (#221f1a), paper is Silkscreen Ground (#f4efe3).
- **Don't** add shadows, glows, or blurs (The Flat Ink Rule).
- **Don't** let Orchid Plate exceed two small strokes per poster (The One Pink Rule).

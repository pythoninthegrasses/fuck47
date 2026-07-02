# Product

## Register

brand

## Users

Politically engaged visitors who already dislike DJT and want a cathartic, entertaining snapshot of his current negative news coverage. They arrive via the domain name (fuckfortyseven.org), which sets expectations: they came for the joke, not for journalism. Context is casual — a quick visit on phone or desktop, shared as a link between like-minded friends. The job to be done: "show me the latest bad news about this guy, and make it look like art."

## Product Purpose

A single-page satirical news site. A backend pipeline (NewsAPI + RSS → DuckDB → LLM sentiment judge) aggregates DJT-related articles, keeps only the negative ones, and a build step injects them into a static page hosted on GitHub Pages. The frontend presents each story as a full-viewport pop-art poster: a rotating DJT image treated as a silkscreen/halftone print dominates the screen, with the article headline set large in punk-flyer lettering and a smaller description beneath. Success looks like: a visitor lands, the poster hits like a gallery piece or a xeroxed gig flyer, they read a few headlines, laugh, and share the link. An archive view (`app/archive/`) provides history over time.

## Brand Personality

Muted pop art meets punk xerox. Two named lineages, each owning one layer:

- **Image treatment — Warhol / Lichtenstein, muted register.** DJT photos processed like misregistered silkscreens: high-contrast black plate over flat, slightly off-register blocks of muted color (the Warhol Jagger print palette — off-white ground, tan, olive, mustard, dusty pink), with halftone/Ben-Day texture where dots serve the print metaphor. Not candy-saturated Lichtenstein primaries; the muted print-shop version.
- **Typography — Raymond Pettibon / Black Flag flyers.** Xerox-black lettering energy: dense ultra-condensed heavy caps for headlines, stencil and hand-scrawled accents, cramped typewriter-style small text for descriptions. Type looks pasted onto the poster, not laid out by a CMS.

Three words: subversive, printed, deadpan. The emotional goal is the smirk of seeing a powerful man rendered as disposable print ephemera — a gig flyer stapled to a phone pole, a screen print run off in someone's garage. Reference artifacts live in `~/Desktop/fuck47/` (`black_flag_raymond_pettibon/`, `pop_art/`).

## Anti-references

- **Generic SaaS/AI slop**: no gradient heroes, card grids, cream-as-default backgrounds, glassmorphism, or anything that reads as a template.
- **Real news outlets**: must not look like a credible news brand (NYT, CNN, BBC). This is parody; visual credibility would undercut the joke.
- **Edgy meme site**: no low-effort meme/4chan energy. The punk roughness is a crafted print aesthetic, not sloppiness.
- **Theme-park pop art**: no full-saturation red/yellow/blue Lichtenstein pastiche, comic "POW!" clichés, or Warhol-grid-of-four gimmicks. The pop art register is muted and specific, not costume.

## Design Principles

- **The poster is the page.** Each article renders as one full-viewport print: image, headline, description composed as a single artwork. Rotation moves between posters, not between UI states.
- **Image dominates, type detonates.** The DJT portrait takes the majority of the viewport; the headline is the loudest typographic element and the punchline. Descriptions stay small and subordinate. No chrome competes.
- **Two lineages, one artifact.** Pop-art treatment lives in the image layer; Pettibon lives in the type layer. Keep the layers distinct and let their collision carry the identity — don't blend them into a generic "retro" wash.
- **Print honesty.** Effects must read as print processes: halftone, posterization, misregistration, xerox grain, paper stock. No digital-native effects (glows, gradients, glass) that break the silkscreen metaphor.
- **Static-site honest.** Everything ships as a GitHub Pages static page (htmx + Alpine only). Image filters happen in CSS/SVG or at build time; no design decision may depend on a runtime backend.

## Accessibility & Inclusion

Best effort, no formal WCAG target. Follow sensible defaults: headlines and descriptions must stay legible over the poster imagery (solid or paper-toned plates behind text where needed), `prefers-reduced-motion` alternatives for the image rotation, semantic HTML, alt text on portraits, keyboard-reachable links. The xerox aesthetic must not come at the cost of legibility.

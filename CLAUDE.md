# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simple static website hosted on GitHub Pages for the domain `fuckfortyseven.org`. The site serves as a placeholder/landing page with political content.

## Architecture

- **Static HTML Site**: Single-page website using plain HTML, CSS, and SVG
- **GitHub Pages Deployment**: Uses `docs/` directory for GitHub Pages hosting
- **Domain**: Custom domain `fuckfortyseven.org` configured via CNAME file

## File Structure

- `docs/index.html`: Main HTML page with inline CSS and SVG graphics
- `docs/CNAME`: Domain configuration for GitHub Pages
- `docs/img/trump.png`: Image asset referenced in the HTML
- `README.md`: Basic project title
- `LICENSE`: Public domain (Unlicense)

## Development

This project has no build process, dependencies, or package management. Changes are made directly to the HTML file.

### Making Changes

- Edit `docs/index.html` directly for content changes
- Images should be placed in `docs/img/` directory
- No build, test, or lint commands are needed - this is a static site

### Deployment

Changes are automatically deployed via GitHub Pages when pushed to the main branch.
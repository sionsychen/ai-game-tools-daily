# AI Game Tools Daily

Curated AI tools and news for game development.

🌐 **Live Site**: https://sionsychen.github.io/ai-game-tools-daily/

## Overview

AI Game Tools Daily is a daily digest of AI-powered tools and technologies relevant to game development. Built with Jekyll and automatically deployed to GitHub Pages.

## Categories

- **AI Art Tools**: Image generation, texture creation, concept art
- **AI Coding**: Code assistants, shader generation, scripting
- **AI Audio**: Sound effects, music generation, voice synthesis
- **AI Animation**: Motion generation, facial animation, physics
- **AI Level Design**: Procedural generation, world building
- **AI Testing**: Automated testing, bug detection, QA tools
- **Industry News**: Product launches, major updates

## Tech Stack

- **Static Site Generator**: Jekyll
- **Styling**: Custom CSS (Tailwind-inspired)
- **Hosting**: GitHub Pages (auto-deploy)
- **Automation**: Python + OpenClaw Cron

## Development

```bash
# Install dependencies
bundle install

# Start development server
bundle exec jekyll serve

# Build for production
bundle exec jekyll build
```

## Content Pipeline

1. Daily automated scraping via OpenClaw Cron (weekdays 11:00 GMT+8)
2. Brave Search API for content discovery
3. Agent-browser for content extraction
4. Jekyll builds and deploys automatically on push
5. Feishu notification for updates

## Project Structure

```
ai-game-tools-daily/
├── _config.yml              # Jekyll configuration
├── _layouts/                # HTML layouts
│   ├── default.html
│   └── post.html
├── _posts/                  # Markdown posts
│   └── YYYY-MM-DD-daily.md
├── _data/
│   └── used_urls.json       # URL deduplication
├── assets/css/
│   └── style.css            # Custom styles
├── scripts/
│   ├── daily-scraper.py     # Content scraper
│   └── daily-run.sh         # Run wrapper
├── index.html               # Homepage
├── categories.html          # Category listing
├── archive.html             # Archive page
└── search.html              # Search page
```

## License

MIT

---

Generated with 🐾 by OpenClaw

# Pratheep // Docs

This is my personal documentation hub — a place to document the architecture, design decisions, and technical write-ups for projects I build. If you want to understand how something I made works under the hood, you're in the right place.

---

## Projects

<div class="grid cards" markdown>

- :material-brain: **ArchiGen**

  ***

  An AI-assisted software architecture generator. Feed it requirements, get back system architecture, tech stack proposals, diagrams (Use Case, ER, Sequence, Class, Flow), and an AI chatbot to discuss tradeoffs.

  Built with a microservices architecture, Google ADK for agentic workflows, and WSO2 Asgardeo for identity management.

  [:octicons-arrow-right-24: View Documentation](Archigen.md)

- :material-console: **Asgardeo CLI**

  ***

  A cross-platform terminal tool for Asgardeo identity management. Supports both a traditional CLI mode and a rich interactive TUI powered by the Charmbracelet ecosystem (Bubble Tea, Huh, Lip Gloss).

  Built in Go with Cobra, Viper, and OS keyring-backed token storage.

  [:octicons-arrow-right-24: View Documentation](Asgardeo_CLI.md)

</div>

---

## About This Site

This site is **not** a portfolio — it is a technical documentation hub. Each page covers the internal workings of a specific project: the architecture choices, the tradeoffs made, the libraries used, and the reasoning behind them.

If you are looking for a high-level overview, start with the project cards above. If you want to go deep, the docs have you covered.

---

## Tech I Work With

- **Languages:** Go, Python, TypeScript, C/C++
- **AI / ML:** Google ADK, Gemini API, Agentic workflows
- **Identity & Auth:** Asgardeo (WSO2), OAuth 2.0 / OIDC
- **Infrastructure:** Docker, PostgreSQL, Redis, FastAPI
- **TUI / CLI:** Bubble Tea, Cobra, Charmbracelet ecosystem

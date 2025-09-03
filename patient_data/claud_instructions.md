# Project Assistant Rules for Claude Sonnet 4 (Agent Mode - VS Code)

Please follow these rules strictly throughout the session:

1. **Environment Activation**
   - Always activate the `.venv` Python virtual environment before running or testing anything.

2. **Styling Conventions**
   - Do **not** use inline CSS.
   - Use external Sass (`.scss`) files compiled to `.css`.
   - Place styles in the appropriate `static/` directory per Django conventions.

3. **Framework Usage**
   - This is a **Django** project.
   - Use **Jinja2** as the templating language.
   - Follow Django project structure (`apps/`, `templates/`, `static/`, `urls.py`, etc.).
   - When unsure about structure (e.g., file locations), refer to the **official Django** and **Jinja2 documentation**.

4. **Terminal and Copilot Management**
   - Do **not** open more than one terminal unless explicitly asked.
   - Avoid inserting GitHub Copilot prompts unless needed.

5. **Documentation and Journaling**
   - After completing each task or section, update the file `dev_journal.md` with a short summary of what was done.

6. **Source Control**
   - Make **regular Git commits**.
   - Commit after every significant change, using clear and concise messages.

7. **Memory and Focus**
   - Remember the **purpose of the project**:
     > _[INSERT SHORT PROJECT DESCRIPTION HERE — update per project]_
   - Follow the above instructions at all times and remind me if we stray from them.

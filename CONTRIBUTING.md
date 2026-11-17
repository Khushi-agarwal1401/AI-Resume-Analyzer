# Contributing to AI Resume Analyzer

Thank you for contributing! Many people here are making their first open
source contribution, so this guide keeps things simple. If something is
unclear, ask in the project forum on Discord.

## 1. Get an issue

1. Look at the [Issues](../../issues) tab and pick one labeled `wocs`.
2. Check its level: `level 1` (beginner), `level 2` (medium), `level 3` (hard).
3. Comment on the issue: "I would like to work on this."
4. **Wait until a maintainer assigns it to you** before you start coding.
5. Work on **one issue at a time**. Do not take several issues together.
   If you become inactive, the issue may be given to someone else.

You can also propose a new idea by opening an issue first. Do not send a big
change without discussing it.

## 2. Set up the project

1. Fork the repository (button on the top right of the repo page).
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/AI-Resume-Analyzer.git
   cd AI-Resume-Analyzer
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run the app: `python app.py` and open http://127.0.0.1:5000

Requirements: Python 3.9+, Flask, pypdf, python-docx.

## 3. Make your change

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/short-description
   ```
2. Make your change. Keep it focused on the issue you were assigned.
3. Test it locally with a real PDF resume and make sure the app still works.
4. Commit with a clear message, for example:
   `feat: add job matcher based on skills` or `fix: handle empty PDF text`.

### Code style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python.
- Use clear names for functions and variables.
- Add a short comment where the logic is not obvious.
- Keep analyzer logic inside the `analyzer/` folder, not inside `app.py`.
- Do not add new libraries unless the issue needs them. If you do, add them to
  `requirements.txt` and mention it in the PR.

### Privacy rules

- **Never commit resumes or any personal files.** The `uploads/` folder must stay
  empty in the repository.
- Do not commit `__pycache__/`, `venv/` or any secret keys.

## 4. Open a pull request

1. Push your branch to your fork and open a PR against `main`.
2. In the PR description write:
   - `Closes #<issue number>`
   - What you changed and why
   - How you tested it (and a screenshot if the UI changed)
   - Whether you used AI (see the AI policy below)
3. A maintainer or mentor will review it. If changes are requested, update the
   same branch and the PR updates automatically.
4. Be patient and polite. Reviews can take a little time.

Maintainers add the `wocs` and `level` labels before merging. The level is
decided by the maintainers/mentors and is final once merged.

## 5. AI policy

AI tools are **allowed** in this project, with these conditions:

- Say in your PR that you used AI and what for.
- You must understand and be able to explain all code you submit.
- Test everything locally. Do not submit code you have not run.

If a contributor breaks these rules, the PR can be closed and the case can be
reported to Team Code Social.

## 6. Winter of Code Social

- Register for WOCS at https://woc.codesocial.tech so your points are counted.
- Points are given only for **merged** PRs that have the correct labels.
- Leaderboard: https://woc.codesocial.tech/leaderboard

## 7. Need help?

Ask in the project forum on the Code Social Discord server (`#find-a-project`),
or comment on your issue. Asking questions is encouraged.

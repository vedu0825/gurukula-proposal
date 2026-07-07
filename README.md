# Layers of Our Education — Gurukula

An interactive pyramid website showing the six foundational layers of Gurukula education. Click any level on the pyramid to read the full text.

## GitHub Pages setup

1. Push this repository to GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
4. Choose the **main** branch and the **/ (root)** folder.
5. Save. Your site will be live at `https://<your-username>.github.io/<repo-name>/` within a few minutes.

## Local preview

Open `index.html` in a browser, or run a simple server:

```bash
python3 -m http.server 8000
```

Then visit http://localhost:8000

## Draw click zones manually

If the pyramid click areas need adjusting, use the outline tool.

If you use the project venv:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python draw_levels.py
```

Or with system Python (if Pillow is already installed):

```bash
python3 draw_levels.py
```

- **Left click** — add a corner point
- **Right click** — undo the last point
- **1–6** — switch level
- **Enter / C** — close the polygon (needs at least 3 points)
- **R** — reset the current level
- **S** — save to `level_coords.json` and show an HTML snippet to paste into `index.html`

Work bottom to top: draw level 1 (orange) first, then 2, and so on. Click the corners of each colored band in order.

## Files

- `index.html` — page structure
- `styles.css` — responsive layout and styling
- `content.js` — text for each pyramid level (from the docx)
- `main.js` — click handling and content display
- `pyramid.png` — pyramid image

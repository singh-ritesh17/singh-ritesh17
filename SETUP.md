# Setup (10 minutes)

1. On GitHub, create a **public** repo named exactly `singh-ritesh17` (same as your username). Tick "Add a README".
2. Upload everything in this folder to it (README.md, scripts/, .github/, cards/, data/, fonts/).
3. Fonts (optional, makes it look much better): download **Instrument Serif** and **Space Grotesk** from Google Fonts,
   put `InstrumentSerif-Regular.ttf` and `SpaceGrotesk[wght].ttf` into `fonts/`.
4. Repo -> Settings -> Actions -> General -> Workflow permissions -> **Read and write permissions**.
5. Repo -> Actions -> "Refresh profile cards" -> **Run workflow**. This fills the contribution graph and re-renders the cards with your fonts.
6. Edit README.md: replace YOUR_INSTAGRAM_HANDLE and YOUR_LINKEDIN, and check the repo links (accreditiq, scholaris, ...) match your real repo names.
7. Edit the CONFIG block at the top of scripts/render_cards.py to change any text, then re-run the workflow.

Preview locally: `STATIC=1 python scripts/render_cards.py` renders the final frame (no animation) for screenshots.

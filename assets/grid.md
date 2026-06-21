# Cover Grid

Canvas: `1600 x 2560`, portrait.

Palette:

- background: `#111314`
- primary ink: `#f6f4ee`
- muted text: `#b8b7b0`
- rule/accent: `#62635f`

Coordinates:

- outer margin: `104`
- metadata stack: author at `y=132`, source/date at `y=244`, both left-aligned.
  The top-right corner is intentionally empty because Kindle library overlays
  badges such as `New` and progress ribbons there.
- top rule: `370`
- title box: starts at `y=452`, uses the full safe content width, and measures
  uppercased title text before choosing font size so long words cannot clip.
- thesis box: starts after the title rule; one or two lines.
- anchor block: starts after the thesis with a minimum `y=1280`; the three
  rows divide the remaining safe height down to `y=2360`. Anchor and descriptor
  sizes are measured inside each row so short three-item summaries reclaim the
  available vertical space.
- bottom rule: `2360`; no product footer/branding text

The grid is intentionally stable across every source type so Kindle library covers read as one series.

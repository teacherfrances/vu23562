# VU23562 homepage

The student homepage for VU23562 Explore community services.
It lists every `vu23562...` activity repo as a stop on a bus route.

Student link: https://teacherfrances.github.io/vu23562/

## How new activities appear

1. Make a new repo whose name starts with `vu23562` (for example `vu23562lesson5foundphone`).
2. Turn on GitHub Pages for it.
3. That's it. Within an hour it shows on the homepage.

Two things keep the list up to date:

- **The hourly update** (`.github/workflows/update-activities.yml`) checks your repos every hour
  and saves the list in `activities.json`. To run it now: Actions tab > Update activity list > Run workflow.
- **The live check** in `index.html` also asks GitHub for new repos when a student opens the page
  (once an hour per device), so a brand-new activity can show up even before the hourly update runs.

## How the homepage sorts things

| Repo name contains | Shown as |
|---|---|
| `lesson1`, `lesson2` ... | That lesson's stop on the route |
| no lesson number | The bonus stop (star) |
| `deck` | Lesson slides |
| `phone` | Found phone game |
| `jeopardy` or `board` | Board game |
| `escape` | Escape room |
| `quiz` | Quiz |
| `record`, `sayit`, `pronun` | Speaking practice |
| anything else | Revision game |

The name on each ticket comes from the `<title>` of the activity page (the part before any colon).
The lesson name comes from that lesson's slide deck title.

## Changing things (settings.json)

```json
{
  "hide": ["vu23562oldgame"],
  "titles": { "vu23562catchthe813": "Catch the 8:13 bus" },
  "lessonNames": { "5": "Out in the community" }
}
```

- `hide`: repos to leave off the homepage.
- `titles`: a different name to show for a repo.
- `lessonNames`: a different lesson name for a stop.

Saving this file runs the update straight away.

---
subsystem_memberships: [UI_AND_OUTPUT]
---
Open the gald3r theme editor: $ARGUMENTS

Activates **g-skl-theme-editor**. Edit gald3r HTML themes against
`docs/themes/theme-schema.json`.

```
@g-theme-edit                      # list themes + open editor (throne app) or fallback menu
@g-theme-edit create <name>        # scaffold docs/themes/<name>.css (@import dark + :root)
@g-theme-edit edit <name> --bg #101018
@g-theme-edit import <path>        # import a :root block / theme file
@g-theme-edit export <name>        # print the theme's editable :root delta
@g-theme-edit preview <name>       # render the reference report with this theme
@g-theme-edit activate <name>      # set html_theme + rewrite _active.css
```

Inside gald3r_throne the visual editor opens (live preview, color pickers,
import/export). Elsewhere the skill uses the file-first fallback. A theme is a
`:root` token override on `gald3r-dark.css`; never edit structural CSS to restyle.

Add a new subsystem to the registry. Activates **g-skl-subsystems** → CREATE SUBSYSTEM SPEC operation.

```
@g-subsystem-add "subsystem-name"
@g-subsystem-add "voice-speech-system" --status planned --tier adv
```

Creates `.gald3r/subsystems/subsystem-name.md` spec file and adds entry to `SUBSYSTEMS.md` registry.
The skill prompts for: name, responsibility, dependencies, dependents, locations (files/folders/skills).

# Flow index

One row per flow. Grep this file for the screen, class, deep link or resource ID a PR touches
before writing anything new. Keep rows sorted by platform, then area.

| Platform | Area | Screen / class | Entry | Flow | IDs it relies on | Text fallbacks | Last verified |
|---|---|---|---|---|---|---|---|
| android | common | Home (`LearningPath`) | cold start | `android/common/launch-home.yaml` | `learning_path_ready` | none | develop `1c55b1db60` |
| android | main-tabs | Main bottom nav: Home, Profile, Challenge | cold start, tab taps | `android/flows/main-tabs/tab-tour.yaml` | `learning_path_ready`, `stat_streak_title`, `placeholder_title` | tab labels `Profile`, `Challenge`, `Home` | develop `1c55b1db60` |

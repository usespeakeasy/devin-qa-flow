# Flow index

One row per flow. Grep this file for the screen, class, deep link or resource ID a PR touches
before writing anything new. Keep rows sorted by platform, then area.

| Platform | Area | Screen / class | Entry | Flow | IDs it relies on | Text fallbacks | Last verified |
|---|---|---|---|---|---|---|---|
| android | auth | Email sign-in with the network off | `pm clear`, cold start, airplane mode | `android/flows/auth/offline-sign-in.yaml` | as above | `An unexpected error occurred\.` | develop `e918e89b7e` |
| android | auth | Cold start while signed in | force-stop, cold start | `android/flows/auth/relaunch-signed-in.yaml` | `home_root_ready`, `onboarding_storybook_sign_in_button` | none | develop `e918e89b7e` |
| android | auth | Settings Log out, sign back in | Home | `android/flows/auth/sign-out-sign-in.yaml` | `action_settings`, sign-in IDs above | `Profile`, `Log out`, `Are you sure you want to sign out\?` | develop `e918e89b7e` |
| android | auth | Email sign-in (`onboarding_sign_in_screen`), premium intro | `pm clear`, cold start | `android/flows/auth/wrong-then-right-password.yaml` | `onboarding_storybook_sign_in_button`, `button_email`, `onboarding_sign_in_*`, `onboarding_premium_intro_(ready\|error)`, `exit`, `home_root_ready` | none | develop `e918e89b7e` |
| android | common | Home (`LearningPath`) | cold start | `android/common/launch-home.yaml` | `learning_path_ready` | none | develop `1c55b1db60` |
| android | common | Profile tab -> Settings | Home | `android/common/open-settings.yaml` | `action_settings` | `Profile`, `Manage Account` | develop `e918e89b7e` |
| android | main-tabs | Main bottom nav: Home, Profile, Challenge | cold start, tab taps | `android/flows/main-tabs/tab-tour.yaml` | `learning_path_ready`, `stat_streak_title`, `placeholder_title` | tab labels `Profile`, `Challenge`, `Home` | develop `1c55b1db60` |
| android | settings | Manage Account (`manage_account_screen`) | Profile, Settings | `android/flows/settings/manage-account.yaml` | `action_settings`, `manage_account_screen`, `edit_name`, `edit_email` | `Profile`, `Manage Account`, the account email | develop `e918e89b7e` |

## Known broken

Flows that failed on the base build and could not be repaired in the run (see Stale IDs in
AGENTS.md). Don't use these as evidence. Remove the entry when the flow passes on base again.

| Flow | Base SHA | Reason |
|---|---|---|

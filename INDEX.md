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
| android | lesson-end | Ask for review dialog over the lesson end (`AskForReviewDialog` entry / `AskForReviewDialogController`), needs the QA-only `Screen.AskForReview` patch and a premium account | Home, lesson deep link, skip cards | `android/common/open-ask-for-review.yaml` | `drill_lesson_skip` | `Are you enjoying learning languages with Speak\?` | develop `7fae598d56` |
| android | lesson-end | Ask for review: Yes, No, Sure!, Not now, Email us, Cancel, back, tap outside | open-ask-for-review | `android/flows/lesson-end/ask-for-review-{yes,no,sure,not-now,email-us,cancel,back,tap-outside}.yaml` | `lesson_end_reskin_root` | button labels, `Glad to hear it\..*`, `Sorry about that.*`, `.*Google Play.*`, `.*[Ss]urvey.*` | develop `7fae598d56` |
| android | main-tabs | Main bottom nav: Home, Profile, Challenge | cold start, tab taps | `android/flows/main-tabs/tab-tour.yaml` | `learning_path_ready`, `stat_streak_title`, `placeholder_title` | tab labels `Profile`, `Challenge`, `Home` | develop `1c55b1db60` |
| android | settings | Manage Account (`manage_account_screen`) | Profile, Settings | `android/flows/settings/manage-account.yaml` | `action_settings`, `manage_account_screen`, `edit_name`, `edit_email` | `Profile`, `Manage Account`, the account email | develop `e918e89b7e` |
| ios | common | AI data consent ("How Speak uses AI") | after sign-in | `ios/common/dismiss-ai-data-consent.yaml` | `ai-data-consent.action.agree`, `home.root.ready` | none | develop `c3a15a89fb` |
| ios | common | Home | cold start | `ios/common/launch-home.yaml` | `home.root.ready`, `ai-data-consent.action.agree` | none | develop `c3a15a89fb` |
| ios | common | Notifications Opt-In preview (`NotificationsEnrollmentScreen`) | Opt-In search results | `ios/common/open-opt-in-preview.yaml` | `BackButton` | `Notifications Opt-In - <name>`, `Set up later`, `Enable` | develop `c3a15a89fb` |
| ios | common | Settings -> Notifications -> Daily Reminders (`CompactDailyRemindersVC`) | Home | `ios/common/open-daily-reminders.yaml` | `Daily Reminders` | `Daily Reminders`, `Allow Daily Reminders` | develop `c3a15a89fb` |
| ios | common | Settings -> Notifications (`CompactNotificationSettingsVC`) | Home | `ios/common/open-notification-settings.yaml` | `Settings`, `Notifications` | `Notifications`, `Daily Reminders` | develop `c3a15a89fb` |
| ios | common | Settings -> Previews (debug preview catalog) | Home | `ios/common/open-previews.yaml` | `Settings` | `Previews`, `Search` | develop `c3a15a89fb` |
| ios | common | Profile tab -> Settings (`SettingsVC`) | Home | `ios/common/open-settings.yaml` | `Settings` | `Profile`, `settings tab icon` | develop `c3a15a89fb` |
| ios | common | Previews search "Notifications Opt-In" | Previews | `ios/common/search-notifications-opt-in.yaml` | none | `Search`, `Notifications Opt-In - (Streak\|Smart Review\|Challenges\|Habit Formation)` | develop `c3a15a89fb` |
| ios | common | Daily Reminders: Allow Daily Reminders on | Daily Reminders | `ios/common/set-daily-reminders-on.yaml` | none | switch value `0`/`1` right of `Allow Daily Reminders`, above `Smart Scheduling` | develop `c3a15a89fb` |
| ios | common | iOS Settings > app > Notifications page | that page | `ios/common/system-allow-notifications.yaml` | `ALLOW_NOTIFICATIONS_ID` (iOS) | switch value right of `Allow Notifications` | iOS 27.0 |
| ios | common | iOS Settings > Apps > Speak Dev > Notifications | any | `ios/common/system-open-app-notifications.yaml` | `com.apple.settings.apps`, `Speak Dev`, `ALLOW_NOTIFICATIONS_ID` (iOS) | `Speak Dev`, `Notifications` | iOS 27.0 |
| ios | common | iOS Settings: Speak Dev notifications off | any | `ios/common/system-notifications-off.yaml` | as `system-open-app-notifications.yaml` | switch value right of `Allow Notifications` | iOS 27.0 |
| ios | common | iOS Settings: Speak Dev notifications on | any | `ios/common/system-notifications-on.yaml` | as `system-open-app-notifications.yaml` | switch value right of `Allow Notifications` | iOS 27.0 |
| ios | notifications | Notifications Opt-In previews: Streak, Smart Review, Challenges, Habit Formation | Home | `ios/flows/notifications/opt-in-previews.yaml` | `BackButton` | as `open-opt-in-preview.yaml` | develop `c3a15a89fb` |
| ios | notifications | Previews search "Notifications Opt-In" lists four previews | Home | `ios/flows/notifications/opt-in-search.yaml` | as `open-previews.yaml` | as `search-notifications-opt-in.yaml` | develop `c3a15a89fb` |
| ios | settings | Daily Reminders off/on, timed hour change, Smart Scheduling on/off | iOS Settings, Home | `ios/flows/settings/daily-reminders-toggle.yaml` | `Daily Reminders`, `PopoverDismissRegion` | `Allow Daily Reminders`, `Smart Scheduling`, `Timed`, `Time Picker`, `.*o.clock`, switch values `0`/`1`; points `73%,32%` (time pill), `50%,90%` (popover dismiss) | develop `c3a15a89fb` |
| ios | settings | Marketing Communications Push toggle (`CompactMarketingCommunicationsView`) | iOS Settings, Home | `ios/flows/settings/marketing-push-toggle.yaml` | `Daily Reminders`, `BackButton`, `Notifications`, `Marketing Communications` | `Marketing Communications`, switch value right of `Push` | develop `c3a15a89fb` |
| ios | settings | Permission off -> Streak toggle -> Allow notifications alert -> iOS Settings -> return, switches enabled | iOS Settings, Home | `ios/flows/settings/notification-permission-enable.yaml` | `Notifications`, `ALLOW_NOTIFICATIONS_ID`, `breadcrumb` | switch value right of `Streak` above `Speak Tutor`, `Allow notifications`, `OFF` | develop `c3a15a89fb` |
| ios | settings | Settings -> Notifications rows | iOS Settings, Home | `ios/flows/settings/notifications-open.yaml` | as `open-notification-settings.yaml`, `system-notifications-on.yaml` | `Marketing Communications` | develop `c3a15a89fb` |

## Known broken

Flows that failed on the base build and could not be repaired in the run (see Stale IDs in
[docs/qa-pr-instructions.md](docs/qa-pr-instructions.md)). Don't use these as evidence. Remove the entry when the flow passes on base again.

| Flow | Base SHA | Reason |
|---|---|---|

# tutor-everywhere

Speak Tutor sheet in lessons (QA of speak-android#8706). Debug Menu flags: `tutor_everywhere_ai_lessons_enabled`, `tutor_everywhere_series_lessons_enabled`, `drill_lesson_tutor_everywhere`.

| Flow | What | Fallbacks |
| --- | --- | --- |
| open-ai-tutor.yaml | AI lesson > tutor button > sheet | point `75%,89%` for the tutor button (ID PR speak-android#8721: `ai_lesson_tutor_button`); text `Ask me anything` |
| open-drill-tutor.yaml | drill deep link > mascot > sheet | point on the mascot avatar; text `Ask me anything` |
| open-series-tutor.yaml | series deep link > `tutor_button_line` > sheet | text `Ask me anything` |
| assert-tutor-open.yaml | sheet showing | text (ID PR: `tutor_everywhere_sheet`) |
| close-tutor-point.yaml | tap a point (close button or outside) | point (ID PR exports `tutor_everywhere_close_button`) |
| close-tutor-back.yaml, press-back.yaml, press-home.yaml | system keys | none |
| close-tutor-swipe.yaml | swipe down from the header | text `Ask me anything` |
| type-question.yaml, ask-suggestion.yaml | ask a question | text `Ask me anything...`, `Switch to voice` |
| tap-point.yaml | tap a point (dictionary button) | point (ID PR: `tutor_everywhere_dictionary_button`) |
| scroll-list-up.yaml, fling-list.yaml | scroll or fling the sheet's Q&A list | point swipes inside the list (no ID on the list; ID PR speak-android#8721 comment: `tutor_everywhere_message_list`) |
| rotate.yaml | set the device orientation (ORIENT) | none. The app is portrait-locked (`screenOrientation="portrait"`), so on phones it does not relayout |
| tap-series-tutor.yaml | series line card > `tutor_button_(line\|restart)` > sheet (before or after the answer) | none |
| assert-tutor-sheet.yaml, assert-series-tutor-card.yaml | sheet showing; for the series card, an initial suggestion (`tutor_everywhere_initial_suggestion`) whose text matches TUTOR_LINE (generated, default `.*(Qué tal\|this).*`) | none |
| assert-series-card.yaml | series card LINE in state STATE_ID (`speak_now_header` / `completed_header`), no sheet | none |
| close-tutor-button.yaml | close button `tutor_everywhere_close_button` | none |
| retry-card-from-tutor.yaml | ask to retry, "Try again in lesson" (`tutor_everywhere_action_button_retry_card`): sheet closes, card back to Speak now | none (the action comes from the tutor's answer to Q) |
| series-tutor-back-resumes.yaml, series-tutor-retry-card.yaml, series-tutor-close-continues.yaml, series-tutor-rotate.yaml | case flows for speak-android#8808 (tutor Back before the answer, Retry card, Back + close button then continue, rotation) | as their parts |
| ask-typed-reply.yaml | sheet > keyboard > type `Q` > send > reply done (`tutor_everywhere_thumbs_up_button`) | none |
| open-dictionary-back.yaml | sheet reply > `tutor_everywhere_dictionary_button` > Expression Details > Back > sheet | none |
| ../debug-demos/tutor-demo-compose.yaml | Debug Menu > Demos > Speak Tutor Everywhere Demo > Compose API > sheet (QA of speak-android#9186) | none |

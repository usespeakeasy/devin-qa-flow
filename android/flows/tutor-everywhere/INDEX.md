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

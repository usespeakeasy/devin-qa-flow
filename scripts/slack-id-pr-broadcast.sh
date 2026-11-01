#!/usr/bin/env bash
# Posts an ID PR announcement as a reply in a #devin-qa-request-mobile QA thread with
# "Also send to channel" on. The Slack MCP's slack_reply_to_thread can't set reply_broadcast.
# Usage: slack-id-pr-broadcast.sh <thread_ts> <text>
set -euo pipefail
thread_ts=${1:?thread_ts}
text=${2:?text}
case "$text" in
  "<@U06CM4TRNBX>"*) ;;
  *) echo "text must start with <@U06CM4TRNBX>" >&2; exit 2 ;;
esac
pid=$(pgrep -f 'node .*mcp-server-slack' | head -1)
token=$(tr '\0' '\n' < "/proc/$pid/environ" | sed -n 's/^SLACK_BOT_TOKEN=//p')
[ -n "$token" ] || { echo "no SLACK_BOT_TOKEN in the Slack MCP process" >&2; exit 1; }
resp=$(jq -n --arg ts "$thread_ts" --arg text "$text" \
  '{channel: "C0C8G9VS2KX", thread_ts: $ts, reply_broadcast: true, text: $text}' \
  | curl -s -H "Authorization: Bearer $token" -H 'Content-Type: application/json; charset=utf-8' \
    --data @- https://slack.com/api/chat.postMessage)
jq -c '{ok, ts, error, subtype: .message.subtype}' <<<"$resp"
jq -e '.ok and .message.subtype == "thread_broadcast"' <<<"$resp" >/dev/null

#!/usr/bin/env bash
# Posts an ID PR announcement as a top-level message in #devin-qa-flow (C0CDW7WKWGN).
# Prints the message ts; put the details in a thread reply to it.
# Usage: slack-id-pr-post.sh <text>
set -euo pipefail
text=${1:?text}
case "$text" in
  "<@U06CM4TRNBX>"*) ;;
  *) echo "text must start with <@U06CM4TRNBX>" >&2; exit 2 ;;
esac
pid=$(pgrep -f 'node .*mcp-server-slack' | head -1)
[ -n "$pid" ] || { echo "Slack MCP server not running; call any slack MCP tool first" >&2; exit 1; }
token=$(tr '\0' '\n' < "/proc/$pid/environ" | sed -n 's/^SLACK_BOT_TOKEN=//p')
[ -n "$token" ] || { echo "no SLACK_BOT_TOKEN in the Slack MCP process" >&2; exit 1; }
resp=$(jq -n --arg text "$text" '{channel: "C0CDW7WKWGN", text: $text}' \
  | curl -s -H "Authorization: Bearer $token" -H 'Content-Type: application/json; charset=utf-8' \
    --data @- https://slack.com/api/chat.postMessage)
jq -c '{ok, channel, ts, error}' <<<"$resp"
jq -e '.ok and .channel == "C0CDW7WKWGN"' <<<"$resp" >/dev/null

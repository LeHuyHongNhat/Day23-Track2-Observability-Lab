#!/bin/sh
# Write Slack webhook URL to a file so alertmanager can read it via api_url_file.
# This avoids Go template env-var resolution issues across alertmanager versions.
echo "${SLACK_WEBHOOK_URL:-https://hooks.slack.com/services/REPLACE/ME}" > /etc/alertmanager/slack-webhook-url
exec /bin/alertmanager "$@"

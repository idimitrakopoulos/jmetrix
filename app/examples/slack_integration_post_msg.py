import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)

slack_token = os.environ["SLACK_BOT_TOKEN"]

client = WebClient(token=slack_token)


def post_to_slack(slack_message, slack_channel):
    try:
        client.chat_postMessage(
            channel=slack_channel,
            text=slack_message
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["error"]


def main():
    # https://app.slack.com/client/T02TJGFUQ/C05HE4M4VPE?cdn_fallback=2
    slack_channel_id = "C05HE4M4VPE"
    post_to_slack("Hello from your app! :tada:", slack_channel_id)


if __name__ == "__main__":
    main()

# CZone Dive Bot 🤿

Facebook Messenger + Instagram auto-reply bot powered by Claude AI.

## Deploy on Render

1. Push this folder to a new GitHub repo (e.g. `czone-dive-bot`)
1. Go to [render.com](https://render.com) → New Web Service
1. Connect the GitHub repo
1. Set Environment Variables:

|Variable           |Value                                 |
|-------------------|--------------------------------------|
|`VERIFY_TOKEN`     |`czonedive_webhook_2025`              |
|`PAGE_ACCESS_TOKEN`|(from Meta Developer → Generate Token)|
|`ANTHROPIC_API_KEY`|(your Claude API key)                 |
|`APP_SECRET`       |(from Meta App Settings → Basic)      |

1. Deploy → copy the Render URL (e.g. `https://czone-dive-bot.onrender.com`)

## Connect to Facebook

1. Go to Meta Developer → CZone Dive Bot → Messenger API Settings
1. **Callback URL**: `https://czone-dive-bot.onrender.com/webhook`
1. **Verify Token**: `czonedive_webhook_2025`
1. Click Verify → Subscribe to `messages` and `messaging_postbacks`
1. Generate Page Access Token → add to Render env vars

## What the bot does

- Customer asks about **courses/prices/booking** → answers from CZone Dive info
- Customer asks about **travel/weather/activities** → Claude answers freely
- Responds in **Thai or English** automatically
- Works on both **Facebook Messenger** and **Instagram DM**

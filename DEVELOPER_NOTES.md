# Developer experience notes

I built this bot to experience the Alpaca Trading API the way a developer does, then looked at what I saw the way I'd look at my own product: where people get stuck, where the experience wins, and what I'd change first.

## The headline: setup is fast

**Under 2 minutes from my Alpaca dashboard to a placed paper order.** That is an excellent time to first value for a brokerage API, and it comes from a few deliberate choices:

- **Keys and the endpoint are on the home screen.** The paper dashboard overview shows the API key, the paper endpoint (`paper-api.alpaca.markets/v2`) and a Regenerate button. I didn't have to go looking for anything.
- **Paper trading starts funded.** There's no deposit, KYC wait or sandbox request. The account is ready to trade the moment you switch to Paper.
- **`alpaca-py` is hard to misuse.** Typed request objects (`MarketOrderRequest`, `StockBarsRequest`) and `TradingClient(paper=True)` meant my order and data calls worked on the first try.
- **The free IEX data feed was enough.** Daily bars for SPY, QQQ and AAPL loaded without any plan upgrade, and the backtest on real prices ran cleanly.

## What I ran

1. `python -m bot backtest --sample`: offline sanity check on synthetic data.
2. `python -m bot backtest`: the same strategy on real daily bars. It worked on the first run.
3. `python -m bot run`: dry run, which printed the signals and the orders it would place.
4. `python -m bot run --place-orders`: placed three paper market orders during market hours.

All three orders showed up in the dashboard right away as positions in **SPY (13 shares), AAPL (29) and QQQ (14)**, each about $9.7K–$9.9K on roughly $100K of paper equity. That's the 10%-per-position cap working as designed, and three orders matches the per-run order cap.

## Where a new developer can still trip

- **Paper vs. live is the first real decision, and it's easy to miss.** Keys belong to an environment. Generate them while looking at the live account and they fail against paper with a generic "unauthorized." I made the bot refuse to start unless `ALPACA_PAPER=true`, so the mistake shows up as a clear setup message instead.
- **The API key is visible on the home screen.** That's great for speed, but people screenshot dashboards (I did, to share my results). The key ID alone isn't enough to trade, yet a masked key with a reveal-and-copy button would keep the speed and cut accidental exposure.
- **My own docs had friction.** Adding keys with `nano`, I pressed Command+O instead of Control+O and got a macOS file dialog. It's a small thing, but it's exactly the kind of first-run snag that makes someone quit, so I added a TextEdit option to the README. The lesson applies to any API: the first five minutes deserve the same care as the API itself.

## What I noticed in the docs while designing Connect

These fed directly into my [Self-Serve Connect concept](https://github.com/ketan-pansare/alpaca-connect-concept):

- **App registration ends in email.** After submitting a Connect app, the next step is that the team follows up by email "to complete the remaining process." A partner gets no status, owner or timeline.
- **Scopes speak developer, not trader.** `account:write`, `trading` and `data` are clear to an engineer, but a trader approving access sees no plain-language explanation or risk level. If `env` is left out, users are asked to authorize live and paper at the same time.
- **The single market-data stream fails late.** A second app using the stream gets error 406, "connection limit exceeded," after the trader has already connected, with no way to choose which app keeps it.

## If I were the PM: what I'd ship first

| Priority | Change | Why | Metric it moves |
|---|---|---|---|
| 1 | **Visible review status for Connect app submissions** (stage, owner, target date) | The developer experience is fast until a partner wants to go live, then it goes quiet. | Days from registration to first live trade through OAuth |
| 2 | **Plain-language, paper-first consent** on top of the existing scopes | Traders approve faster when they understand what they're granting, and starting on paper lowers the risk of saying yes. | Consent completion rate; paper-to-live graduation |
| 3 | **Masked API key with reveal and copy** on the dashboard | Keeps the 2-minute setup while reducing exposure in screenshots and screen shares. | Key regenerations caused by exposure (support tickets) |
| 4 | **Choose which app gets the data stream** before connecting | Turns a late 406 error into a choice the trader makes up front. | Support tickets mentioning error 406 |

The core API experience is already strong, so the biggest gains are at the edges: the moment a partner goes from paper to live, and the moment a trader decides whether to trust an app.

— Ketan Pansare

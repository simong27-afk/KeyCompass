---
title: How to move crypto from exchange to hardware wallet — KeyCompass
description: Step-by-step: withdraw crypto from an exchange to your own hardware wallet, pick the right network, check the address and send a test amount first.
category: Getting started
published: 2026-10-07
checked: 2026-10-07
featured: no
---
# How do I move crypto from an exchange to a hardware wallet?

> Moving your crypto off an exchange is one of the most important steps in self-custody, and
> one of the easiest to get wrong. Here is how to do it carefully, one step at a time.

**The short answer.** Set up your hardware wallet and test your backup first. Then, in the
wallet's own app, get a receiving address for the right coin and network, and check it on the
hardware wallet's screen. On the exchange, withdraw a small test amount to that address, on the
same network, and wait until it arrives. Only then send the rest. Never type your recovery
phrase into the exchange, a website or an app: no exchange ever needs it to send you your own
coins.

People describe this in different ways: withdrawing to a cold wallet, moving to cold storage,
transferring from Coinbase or Kraken to Ledger or Trezor, or simply taking self-custody.
Everything below applies whichever exchange and hardware wallet you use.

- Before you start
- Step 1: Set up the hardware wallet and test the backup
- Step 2: Prepare your exchange account
- Step 3: Get a receiving address and check it on the device
- Step 4: Choose the right network
- Step 5: Send a small test amount
- Step 6: Send the rest
- Step 7: Afterwards
- If your crypto hasn't arrived
- Mistakes that cost people money

## Before you start

- **Buy the hardware wallet from the maker or an authorised reseller,** not from a marketplace
  seller. If a device arrives with a recovery phrase already printed or written on a card,
  do not use it: a genuine hardware wallet always creates the phrase itself, on its own screen.
- **Download the wallet's app only from the maker's own website.** That means Ledger Wallet from
  ledger.com and Trezor Suite from trezor.io. Fake versions of both are advertised in search
  results and on lookalike sites, and they exist to steal recovery phrases. Type the address
  yourself rather than clicking a search ad.
- **Give yourself time.** Allow an hour or two for a first transfer, at a moment when you are not
  rushed or distracted. Some exchanges hold a new withdrawal address for a day or more before you
  can use it, so you may need to come back to finish.
- **Work somewhere private,** with no one looking over your shoulder and no cameras pointing at
  your screen or your backup.

## Step 1: Set up the hardware wallet and test the backup

Set up the device by following the maker's instructions, write down the recovery phrase it shows
you, and choose a PIN. Then, before any money goes near it, check that the backup you wrote down
is correct. Ledger and Trezor both have a built-in check that does this without wiping the device:
see [How to test your recovery phrase backup safely](https://keycompass.co.uk/guides/test-recovery-phrase-backup).

It is tempting to skip this step and come back to it later. Don't. Once your savings are on the
device, a backup with a single wrong word is the difference between losing a device and losing
everything on it.

## Step 2: Prepare your exchange account

- **Secure the account.** Use an authenticator app or a security key for two-factor
  authentication, not text messages, if your exchange allows it.
- **Unstake or unlock anything that is earning.** Coins in staking, savings or "earn" products
  usually have to be moved back to your ordinary balance before you can withdraw them, and some
  take days to unlock.
- **Check the withdrawal fee and minimum.** Exchanges charge a fee for each withdrawal and often
  have a minimum amount. This matters for how large your test amount needs to be.
- **Expect a few questions.** Since September 2023, UK exchanges have had to follow the Travel
  Rule, which means they may ask where a withdrawal is going. When asked, say it is a wallet you
  own and control yourself, sometimes called a self-hosted or unhosted wallet. Some exchanges ask
  you to confirm this with a simple declaration; some ask for a small test transaction. Neither
  involves your recovery phrase.

## Step 3: Get a receiving address and check it on the device

A receiving address is the public address your crypto is sent to. It is safe to share; it is
not the same as your recovery phrase.

1. **Open the wallet's app and add an account for the coin you are moving.** In Ledger Wallet
   you add an account for that coin (installing the coin's app on the device if asked). In Trezor
   Suite you turn on the coin in the settings if it isn't already showing.
2. **Choose Receive** for that account.
3. **Check the address on the hardware wallet's screen.** The app will show an address and ask
   you to confirm it on the device. Compare the two carefully, the whole address, not just the
   first and last few characters. The device's screen is the one you can trust: if malware on
   your computer has swapped the address, the device will show a different one.
4. **Copy the address from the app** once the device has confirmed it.

Get a fresh address from your wallet each time you receive. Never copy an address out of an
old transaction or your exchange's history, which is how address poisoning scams catch people
(more on that below).

## Step 4: Choose the right network

This is where most expensive mistakes happen. Many coins and tokens can be sent on more than one
network. USDT, for example, may be offered on Ethereum, Tron, Solana and others. When you withdraw,
the exchange asks you to pick one.

- **Pick the network that matches the account you created in your wallet.** If you added a
  Bitcoin account, withdraw on the Bitcoin network. If you added an Ethereum account to receive
  a token, withdraw on Ethereum.
- **The cheapest network is not always the right one.** An exchange may list a network your
  hardware wallet does not support, or one you have not added. Crypto sent that way may not show
  up in your wallet, and getting it back can be difficult or impossible.
- **Ignore the memo or tag field** unless your wallet's app asks for one. Exchanges use memos and
  tags (common with XRP, XLM and some others) to tell customers apart. When sending to your own
  hardware wallet, you normally leave it blank. If the exchange won't let you continue without one,
  stop and check the maker's guidance for that coin before going on.
- **Tokens need a little of the network's own coin to move later.** You don't need any to
  *receive* tokens on Ethereum, but when you eventually want to send them on you'll need a small
  amount of ETH in the same account to pay the network fee. The same applies on other networks.

If you are unsure which network to use, stop. Check the maker's list of supported coins and
networks, or ask someone who knows, before sending anything.

## Step 5: Send a small test amount

1. **Paste the address into the exchange's withdrawal form** and compare it against your
   hardware wallet's screen one more time.
2. **Choose the network** from Step 4.
3. **Send a small amount,** enough to clear the exchange's minimum and fee, but an amount you
   could afford to lose if something were wrong.
4. **Approve the withdrawal** with your exchange's two-factor confirmation.
5. **Wait for it to arrive** in your wallet's app. It can take from a minute to an hour or more,
   depending on the network and the exchange.

When it arrives, check the amount in your wallet's app against what you sent, less the fee.
That one small transaction proves the address, the network and the account are all right.

If the exchange asked you to add the address to an address book or allowlist, this is a good time
to do it, so later withdrawals can only go to addresses you have approved.

## Step 6: Send the rest

Withdraw the remaining balance to the same address, on the same network, checking the address
again before you confirm. If the amount is large, there is nothing wrong with sending it in two or
three parts. It costs a little more in fees but limits the damage of any mistake.

Remember the fee: the exchange usually takes it from the amount you are withdrawing, so a
"withdraw all" is the easiest way to leave nothing behind.

## Step 7: Afterwards

- **Check everything has arrived,** for every coin and network you moved.
- **Keep a record** of each withdrawal: the date, amount, coin, network and the transaction ID
  the exchange shows you. For UK tax, moving crypto between wallets you own is generally not a
  disposal, but a withdrawal fee paid in crypto may be. Your records make this easy for you or
  your accountant to work out later. (This is not tax advice.)
- **Decide what to do with the exchange account.** Many people keep it open for buying and selling,
  with only what they need on it. If you keep it, keep its security up to date.
- **Store the hardware wallet and the backup separately.** Someone who finds both together has
  everything they need.
- **Be careful who you tell.** The fewer people who know you hold crypto, and how much, the better.

## If your crypto hasn't arrived

1. **Don't panic and don't send more.** Most delays are just a busy network or an exchange
   processing withdrawals in batches.
2. **Find the transaction ID** in the exchange's withdrawal history. If there isn't one yet, the
   exchange hasn't sent it.
3. **Check the transaction on a block explorer** for that network, using the transaction ID. It
   will show whether the transaction has been confirmed and which address it went to.
4. **Check you're looking at the right account** in your wallet's app, on the right network.
   Tokens sometimes need to be added to the app before they show, even though they arrived.
5. **If it went on the wrong network or to the wrong address,** contact the exchange through its
   own website or app, never through a phone number or account you found on social media. Some
   network mistakes can be fixed; some cannot.

Be wary of anyone who contacts you offering to recover lost crypto, especially after you have
posted about a problem online. "Recovery services" that reach out to you, or ask for a fee up
front or your recovery phrase, are scams.

## Mistakes that cost people money

- **Typing the recovery phrase into anything other than the hardware wallet.** No exchange,
  wallet maker or support team ever needs it. Anyone who asks for it is trying to steal from you.
- **Skipping the test amount.** It costs one extra fee and takes a few minutes. It is the cheapest
  insurance there is.
- **Choosing the wrong network** because it was cheapest, or listed first.
- **Copying an address from transaction history.** In an address poisoning scam, someone sends
  you a tiny amount from an address made to look almost identical to yours, hoping you'll copy it
  next time. Always get the address fresh from your wallet and check it on the device.
- **Not checking the address on the device's screen.** Malware can change an address on your
  computer between copying and pasting. The device's screen is the only place you can trust.
- **Downloading a fake wallet app.** Get Ledger Wallet and Trezor Suite only from ledger.com and
  trezor.io.
- **Rushing.** Scammers and mistakes both thrive on urgency. If something feels wrong, stop.

## Getting help

If you would rather not do your first transfer alone, a KeyCompass onboarding session covers
everything on this page, live on a video call. You do every step yourself, on your own device,
while we go through it with you: setting up the hardware wallet, checking the backup, picking the
right network, sending the test amount and confirming it has landed, then moving the rest. You
finish with a written record of your setup.

KeyCompass never asks for your recovery phrase, a photo of it or any part of it, and never holds
your crypto. Anyone who does ask, whatever they claim to be, is attempting to steal from you.

[See pricing for onboarding sessions](https://keycompass.co.uk/pricing#private-onboarding-session)

If you already have crypto on a hardware wallet, read [How to test your recovery phrase backup safely](https://keycompass.co.uk/guides/test-recovery-phrase-backup).

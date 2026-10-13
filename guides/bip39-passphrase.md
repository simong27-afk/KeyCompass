---
title: BIP39 passphrase (25th word): should you use one? — KeyCompass
description: What a BIP39 passphrase is, how hidden wallets work on Ledger and Trezor, what it protects against, the risks, and how to set one up and test it safely.
category: Backups
published: 2026-10-12
checked: 2026-10-12
featured: no
---
# What is a BIP39 passphrase, and should I use one?

> A passphrase adds a second secret on top of your seed phrase. It can make a found backup
> useless to a thief. It can also lock you, or your family, out for good.

:::answer
A BIP39 passphrase is an extra word or phrase you choose yourself and add
to your seed phrase. Together they open a separate "hidden wallet" that the seed phrase alone
cannot reach. Its strength is that someone who finds your seed phrase still can't take the crypto
behind the passphrase. Its weakness is that if you forget the passphrase, or write it down wrongly
by a single character, that crypto is gone, even with the seed phrase in your hand. For most
people the better first step is storing and testing the seed phrase properly. A passphrase is worth
adding only once you are confident you can back it up and pass it on as carefully as the words
themselves.
:::

It goes by several names: passphrase, BIP39 passphrase, 25th word (or 13th word, with a 12-word
phrase), hidden wallet or passphrase wallet. It is not the same as your device PIN or a password
for a wallet app.

- How a passphrase works
- What it protects against, and what it doesn't
- The risks
- Should you use one?
- How to set one up safely
- On Ledger and Trezor
- Test it before you fund it
- How to back up a passphrase
- Mistakes to avoid

## How a passphrase works

Your seed phrase on its own opens your normal wallet, sometimes called the standard wallet. Add
a passphrase and you get a completely different wallet, with different addresses and its own
balance. Change the passphrase by one letter and you get yet another wallet.

:::rule The key point
**There is no such thing as a wrong passphrase.** Every passphrase opens a
valid wallet. Type yours slightly wrong and you won't see an error, just an empty wallet. That is
deliberate, because it stops anyone telling whether a wallet with a passphrase exists, but it
also means a typo looks exactly like "nothing here".
:::

Your passphrase is never stored on the device or in the wallet app. You enter it each time you
want the hidden wallet, or on some devices you link it to a second PIN.

## What it protects against, and what it doesn't

It protects you if:

- **Someone finds your seed phrase.** A burglar, a nosy visitor or a family member who comes across
  your backup gets only the standard wallet, which can be left empty or hold a small amount.
- **Someone forces you to unlock your device.** You can open the standard wallet, with a modest
  balance in it, while the main holdings stay behind the passphrase.

It does not protect you if:

- **You type it into a compromised computer or phone.** Malware can record it. Enter it on the
  device itself wherever possible.
- **The passphrase is stored with the seed phrase.** Then anyone who finds one finds both.
- **You forget it, or nobody else knows it exists.** No one can recover it for you: not the wallet
  maker, not support, not KeyCompass.

## The risks

A passphrase swaps one risk for another. It reduces the risk of theft from a found backup, and
increases the risk of loss.

- **It's a second thing you can't lose.** Lose the passphrase and the hidden wallet is gone for
  good, even with a perfect seed phrase.
- **Small mistakes are fatal.** Passphrases are case-sensitive, and a space counts as a character.
  "Blue Car" and "blue car" open different wallets, and a trailing space opens another.
- **It complicates inheritance.** Your family needs the seed phrase, the passphrase, and the
  knowledge that a passphrase exists at all. An heir who opens the standard wallet and finds it
  empty may reasonably assume there is nothing there.
- **More complexity, more mistakes.** Some self-custody professionals advise most clients not to
  use one at all, because more people lose funds through over-complicated setups than through
  theft of a well-stored backup.

## Should you use one?

There is no single right answer, but this is a reasonable guide.

**Probably not yet if:**

- you haven't yet tested your seed phrase backup, or aren't sure it is stored well
- you'd struggle to keep a second backup safe, separate and findable
- your family would need to recover the wallet without help
- you already use multisig, which removes the single point of failure in a better-structured way

**Worth considering if:**

- your seed phrase backup is well stored and tested, and you want protection in case it is found
- you can store the passphrase separately, as durably, and make sure the right person can find
  both
- you are comfortable entering it on the device each time, and testing it regularly

If you are unsure, start without one. You can always add a passphrase later: it creates a new
hidden wallet, and you move funds into it once it is tested.

## How to set one up safely

1. **Test your seed phrase first.** A passphrase is useless on top of a broken backup. See
   [How to test your recovery phrase backup safely](https://keycompass.co.uk/guides/test-recovery-phrase-backup).
2. **Choose a passphrase you can write down exactly.** Long enough to be hard to guess (several
   random words is a good approach), but without ambiguous characters or spacing you might
   misremember. Avoid anything personal, like names or dates.
3. **Write it down before you use it,** on paper or metal, exactly as you will type it, including
   capitals and spaces.
4. **Enter it on the device,** not on the computer, wherever your device allows.
5. **Test it before you send anything** (see below).
6. **Store the passphrase backup somewhere different from the seed phrase.**

## On Ledger and Trezor

:::tabs Choose your device
::tab Ledger | Temporary, or linked to a second PIN
Ledger devices offer two ways to use a passphrase, both set up on the device itself:

- **Temporary passphrase.** You enter it on the device whenever you want the hidden accounts. It
  stays active only until the device is switched off.
- **Passphrase linked to a second PIN.** You set the passphrase once and choose a second PIN. At
  start-up, your normal PIN opens your normal accounts and the second PIN opens the hidden ones.

The passphrase can be up to 100 characters, and is case-sensitive. As with your main PIN, three
wrong PIN attempts reset the device, so you'll need your seed phrase backup and your passphrase to
get back in. Hidden accounts then appear in Ledger Wallet as a separate set of accounts.
::tab Trezor | Passphrase wallets in Trezor Suite
In Trezor Suite, passphrase wallets are switched on under **Settings → Device → Use passphrase
wallets**. When you open the wallet, you choose the standard wallet or enter a passphrase to open
a passphrase wallet (Trezor calls these hidden wallets).

- **Enter it on the device where you can.** Trezor Safe 3, Safe 5, Safe 7 and Model T let you type
  the passphrase on the device itself.
- Trezor Suite accepts passphrases of up to 50 characters, and they are case-sensitive.
- Trezor points out that an empty wallet does not prove you typed the passphrase correctly. It may
  just be a different, empty wallet.

:::warn On a Trezor Model One
The Model One can't take a passphrase on the device, so it is typed on the computer. That is a real
weakness if the computer is ever compromised.
:::
:::

## Test it before you fund it

This is the step most people skip, and the one that matters most.

1. Open the passphrase wallet and **write down its first receiving address** (or the last eight
   characters of it, and which coin it is for).
2. **Close it and reopen it,** typing the passphrase fresh from your written copy, not from memory.
3. **Check the first receiving address matches** on the device's screen.
4. **Send a small test amount,** then repeat the reopen-and-check once more.
5. Only then move the rest.

Repeat the reopen-and-check whenever you test your seed phrase, at least once a year.

## How to back up a passphrase

Treat the passphrase backup with the same care as the seed phrase, but never in the same place.

- **Written exactly,** in capitals or with a note where case or spacing matters.
- **Durable,** on metal if your seed phrase is on metal.
- **Separate,** so that no single discovery gives someone both.
- **Findable,** by the right person, along with a note that a passphrase exists. See
  [Crypto inheritance and family access](https://keycompass.co.uk/inheritance).

For more on materials and locations, see
[Seed phrase storage: where should I keep mine?](https://keycompass.co.uk/guides/seed-phrase-storage)

## Mistakes to avoid

- **Typing your real seed phrase or passphrase into a website,** including well-known BIP39 tools
  and "generators". Even a trusted page is still a connected computer.
- **Falling for "seed phrase with balance" offers.** Lists and tools claiming to give you seed
  phrases for funded wallets are scams. See [how to spot crypto scams](https://keycompass.co.uk/guides/crypto-scams-uk).
- **Keeping the passphrase with the seed phrase,** which defeats the point.
- **Forgetting which wallet holds the funds.** Note, somewhere safe, that a passphrase wallet exists.
- **Adding a passphrase in a hurry,** for example after a scary headline. A rushed change with an
  untested backup is far more likely to lose you funds than the threat you were reacting to.

## Getting help

Whether a passphrase is right for you depends on how much you hold, who you live with and who
would need to recover it. A KeyCompass security review looks at exactly that, along with your
backups and succession, without ever seeing your words or your passphrase.

KeyCompass never asks for your recovery phrase, your passphrase, a photo of either or any part of
them. Anyone who does, whatever they claim to be, is attempting to steal from you.

[How a security review works, and what it costs](https://keycompass.co.uk/security-review)

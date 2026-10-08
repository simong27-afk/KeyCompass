---
title: How to test your recovery phrase backup safely — KeyCompass
description: How to check your seed phrase backup works without exposing it: the built-in checks on Ledger and Trezor, passphrases, multisig, and what to do if it fails.
category: Backups
published: 2026-10-07
checked: 2026-10-08
featured: no
---
# How do I test my recovery phrase backup?

> The only way to know a backup works is to check it, on the hardware wallet itself and
> never on a phone or computer. Here is how to do that safely, and what to do if it fails.

**The short answer.** Most hardware wallets can check your written recovery phrase against
the one stored on the device, without wiping anything. You type the words in on the device's
own screen and it tells you whether they match. On Ledger that is the Recovery Check app; on
Trezor it is Check backup in Trezor Suite. It takes about ten minutes, and it is the single
most useful thing you can do for a wallet you already own. If the check fails, your funds are
still safe for now, but you need to move them to a new wallet with a backup you have tested.

The recovery phrase is also called a seed phrase, mnemonic, or 12 or 24 words. Everything
below applies whichever name your wallet uses.

- Why test a backup at all
- The one rule: never type it into anything connected
- Before you start
- The built-in check on Ledger and Trezor
- Restoring on a second device
- If you use a passphrase
- If you use multisig
- Check the backup itself, not just the words
- When to test
- If the check fails

## Why test a backup at all

A backup you have never tested is a hope, not a backup. The mistakes are small and ordinary:
a word misspelt, two words swapped, a word missed while copying, ink that has faded, or
handwriting that made sense on the day and does not now. None of them show up until the day
you need the backup, which is usually the day the device has been lost, broken or stolen.

There is a second reason to test while everything still works. Hardware devices such as Ledger and Trezor do not show you the recovery phrase again after setup. If your written copy is wrong,
there is no way to read the correct words off the device and fix it. Finding the problem while
the device still works turns a potential total loss into an afternoon's inconvenience.

## The one rule: never type it into anything connected

Your recovery phrase should only ever be entered on the device itself. Never type it
into a phone, a computer, a website, a wallet app, a password manager or a notes app, and never
photograph it.

Any website, app or person offering to "validate", "verify" or "check" your recovery phrase is a
scam, whatever it looks like and whoever it claims to be. A legitimate check never needs your words
to leave the device.

## Before you start

- **Choose somewhere private.** Away from other people, and away from cameras: laptop webcams,
  video doorbells and phones propped up nearby all count.
- **Have everything to hand:** the device, its PIN, and every part of your backup.
- **Write down your first receiving address.** Open the account in Ledger Wallet or Trezor Suite and
  note the first receiving address, or just its first and last six characters. It is not secret,
  and it gives you something to compare against if you ever restore the wallet.

## The built-in check on Ledger and Trezor

This is the method to use if your device offers it. Nothing is wiped, and your words are entered
on the device, never on the computer.

### Ledger: the Recovery Check app

1. Connect your Ledger and open Ledger Wallet.
2. Go to the section that manages apps on your device (My Ledger) and install **Recovery Check**,
   Ledger's own app.
3. Open Recovery Check on the device and choose how many words your phrase has: 12, 18 or 24.
4. Enter each word, in order, using the device's buttons or touchscreen.
5. The device tells you whether the phrase matches the one it holds.

You can uninstall the app afterwards. It does not change anything stored on the device.

### Trezor: Check backup

1. Connect your Trezor and open Trezor Suite.
2. Open the device settings (the gear icon) and select **Check backup** in the wallet backup
   section.
3. Enter each word, in order, on the device's own screen.
4. The device confirms when the backup matches.

The device is not wiped. It compares the words you enter with the backup it already holds.

**On a Trezor Model One,** choose **Advanced recovery** when Suite asks how to enter your words.
The Model One cannot take words on the device itself, so the standard method has you type them
into the computer. With Advanced recovery the letters appear only on the Trezor's screen and you
click matching positions on a scrambled grid in Suite, so your words never reach the computer.
It is slower, but it keeps to the one rule above.

### Other hardware wallets

Most others have an equivalent, often called "verify seed", "check backup" or "dry run recovery",
in the device settings. Follow the maker's own instructions, from their official website, and
never from a link in an email, an advert or a search result you have not checked.

## Restoring on a second device

If you have a spare device, you can go one step further: restore your backup onto it and
confirm the first receiving address matches the one you wrote down. This proves the backup would
rebuild your wallet on a device that has never seen it, which is exactly what happens in a real
recovery. Wipe the spare device afterwards.

Two warnings. Never restore your phrase into a phone or desktop wallet app to test it, because
that puts your words on an internet-connected device. And never wipe your only device to test the
backup: if the backup turns out to be wrong, you will have destroyed the only working copy of
your wallet.

## If you use a passphrase

Some people add a passphrase, sometimes called a 25th word, on top of the recovery phrase. The
built-in checks above only confirm the 12 or 24 words. They say nothing about the passphrase.

To test it, unlock the passphrase wallet on your device and confirm you see the account you
expect, ideally by checking its first receiving address. A passphrase that is wrong by a single
character does not produce an error. It opens a different, empty wallet, which is why this step
matters and why it is easy to get wrong without noticing.

## If you use multisig

In a multisig wallet, testing each key's recovery phrase is necessary but not enough. Recovering
the wallet also needs its configuration, often called a wallet descriptor or configuration file,
which records the public keys involved and how many signatures are required. Without it, recovery
can become very difficult or impossible even with every phrase in hand.

Check each key's backup with the method for that device, then confirm a copy of the configuration
exists and that the people who would need it know where it is.

## Check the backup itself, not just the words

A backup can contain the right words and still let you down. While you have it out:

- **Could someone else read it?** Your family may be the ones using it. Every word should be clear
  to a stranger, not just to you.
- **Are the words numbered?** Order matters as much as the words do.
- **Check the spelling against the official list.** Recovery phrases use a fixed list of 2,048
  English words, and the first four letters of each word are unique. That helps when handwriting
  is ambiguous, and it means a word that is not on the list is certainly a mistake.
- **Is it holding up?** Paper fades, gets damp and tears. Stamped metal survives far more, but
  check every letter was stamped clearly.
- **Is it where you think it is,** and protected against fire, flood and the people who share
  your home?
- **Would anyone know it exists?** If you died tomorrow, could the right person find it and know
  what it is for, without the wrong person being able to?

## When to test

- **Straight after setting up a wallet,** before moving more than a small amount into it.
- **Once a year.** Pick a date you will remember, such as the start of the tax year.
- **After anything that might have changed it:** moving house, a leak or fire, a new or replacement
  device, or moving the backup somewhere new.

## If the check fails

First, do not panic. Your device still works, so your funds are safe for now. But until they are
moved, that device is the only working key to your wallet, so treat it carefully: do not reset it,
lend it or update it until you have finished.

Do not try to fix the backup by guessing or rearranging words. The device cannot show you the
correct phrase, and a wrong backup that looks fixed is worse than one you know is wrong.

Instead, move your funds to a new wallet with a backup you know works:

1. **Set up a new wallet** on a second device, creating a new recovery phrase.
2. **Write the new phrase down carefully, then test it** with the built-in check before you go
   any further.
3. **Send a small test amount** from the old wallet to the new one and confirm it arrives.
4. **Move the rest,** then check every account and network you hold has been moved.
5. **Only then reset the old device** and destroy the faulty backup securely.

If you have more than one account or network, or use a passphrase or multisig, take this slowly
and check each step before the next.

## Getting help

KeyCompass checks backups as part of every security review, without ever seeing your words.
You enter them on your own device; we walk you through the check and the rest of your setup,
and give you a written list of anything that needs fixing. If you just want to ask a few
questions, a drop-in hour covers that.

KeyCompass never asks for your recovery phrase, a photo of it or any part of it. Anyone who does,
whatever they claim to be, is attempting to steal from you.

[See pricing for security reviews and drop-in hours](https://keycompass.co.uk/pricing)

If you think your phrase is already lost, read [I've lost my recovery phrase. What now?](https://keycompass.co.uk/lost-recovery-phrase)

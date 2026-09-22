# I've lost my recovery phrase. What now?

> What can still be recovered, what genuinely cannot, and how to tell which situation
> you are in — without handing your money to someone promising a miracle.

**The short answer.** If your recovery phrase is gone and you can no longer open the wallet
on any device, the funds are almost certainly unrecoverable. That is not a policy anyone can
appeal; it is how the cryptography works. Nobody — not the wallet maker, not an exchange, not
a recovery service — holds a copy. But a great many people who believe their phrase is lost
are actually in a different situation, and several of those situations are fixable. Work
through the checks below before you conclude anything.

- Stop and do not wipe anything
- First: is it actually lost?
- The situations that are usually recoverable
- The situation that is not
- Why "recovery services" are how people lose the rest
- What to do once you know where you stand

## Stop and do not wipe anything

Before anything else: do not factory reset, wipe, update or sell any phone, laptop or
hardware wallet that has ever held this wallet. Do not uninstall the app. Do not "start
fresh" to try again.

People in a panic very often destroy the one remaining copy of their keys while trying to fix
the problem. If the wallet software is still installed somewhere and still opens, the keys are
still there, and that is a recoverable position. A factory reset ends it permanently.

If the device is old and switched off in a drawer, leave it exactly as it is until you have
read the rest of this page.

## First: is it actually lost?

There is a real difference between a phrase that is *missing* and one that is *gone*, and most
people arrive here having decided too quickly that it is gone. Before accepting that, search
properly and methodically rather than from memory.

Recovery phrases are usually written at the moment a wallet is set up, often on whatever was
to hand. Look for a single sheet of paper, a card that came in the box with a hardware wallet,
a page torn from a notebook, or a metal plate. Check anywhere you keep documents you rarely
touch: a passport folder, a filing box, a safe, a book on a shelf, the back of a picture
frame, a drawer in a house you have since moved out of. Ask whether you gave a copy to a
partner or family member for safekeeping, or posted it to yourself.

If you set the wallet up at a particular desk or in a particular room, the phrase was probably
written within a few feet of where you were sitting.

## The situations that are usually recoverable

Most people who think they have lost access are in one of the following positions rather than
the truly unrecoverable one. Each of these has a genuine route back, and none of them requires
paying anybody for a miracle.

### The wallet is still installed on a device you can unlock

This is the single most common case, and the most commonly missed. Your recovery phrase is a
backup of the keys — but the keys themselves are still sitting in the wallet app. If the app
is still on your phone or computer and you can still unlock it with its PIN, password or
biometrics, you have not lost access to anything.

Most software wallets will show you the recovery phrase again from inside the app, usually
under settings, security or backup, after you re-enter the password. Write it down properly
this time, verify it, and store it offline.

If the wallet will not display the phrase again, you can still move the funds: send everything
to a new wallet whose recovery phrase you have written down and checked first.

### A hardware wallet you can still unlock

If you still have the device and you still know the PIN, you still have your funds. The keys
live on the device, not on the paper. The paper is only the spare.

Modern hardware wallets will generally not re-display a recovery phrase once it has been set
up, for good security reasons — so do not expect to read it back off the device. What you can
do is set up a second wallet, back that one up properly and verify it, then transfer
everything across. Do that before the device is lost, broken or wiped by failed PIN attempts.

### You have some of the words but not all of them

A recovery phrase is not a random list. It is drawn from a fixed list of 2,048 words, and the
phrase as a whole carries a checksum — a mathematical consistency check built into the
standard. That means a phrase with one or two words missing can often be reconstructed,
because only a small number of candidate words produce a valid phrase at all.

This is a genuine, legitimate technical recovery path and it does work. It has one absolute
rule: this must be done offline, on a device that is not connected to the internet. Any
website, app or service offering to "complete" or "check" a partial recovery phrase for you is
collecting phrases. There is no exception to this.

### A word you cannot read, or that is not on the list

Because the word list is fixed and every word on it is uniquely identified by its first four
letters, ambiguous handwriting is often resolvable. A word written as "abandn" is only ever
"abandon". A character you cannot tell is a 1 or an l, an 0 or an O, usually has only one
reading that produces a real word from the list.

If a word you have written is not on the list at all, it was mis-transcribed at the time, and
the nearest valid word is usually obvious once you compare it against the list.

### The phrase works, but the wallet shows nothing

This is the case that frightens people most and is very often not a loss at all. If you
restore a phrase and the balance comes back as zero, the most likely explanations are:

A passphrase was set and has been forgotten. Some wallets allow an extra word of your own
choosing on top of the standard phrase, sometimes called a 25th word. The same phrase with and
without it produces two entirely different wallets, both valid, and the one without shows
empty. The phrase is not lost — the passphrase is, which is a different problem.

The wallet was restored into different software that looks in a different place. Wallets can
derive addresses in more than one way, and restoring a correct phrase into an app expecting a
different scheme can show an empty account while the funds sit untouched on the chain. Trying
the same phrase in the wallet software it was created with usually resolves it.

The funds are on a different account or network within the same wallet. Many wallets hold
several accounts behind one phrase, and only show the first by default.

In all three cases the money has not moved. You are looking in the wrong place with the right
key.

## The situation that is not recoverable

If the recovery phrase is genuinely gone, no copy exists anywhere, and the wallet cannot be
opened on any device you still have, then the funds cannot be recovered by anyone.

This is worth being plain about rather than soft, because the softness is what scammers sell
into. Self-custody means no organisation holds a copy of your keys. That is the entire point
of it, and it is what protects you from a company freezing your funds, going under, or being
compelled to hand them over. The same property means there is no reset, no support ticket, no
identity check that restores access. The coins remain visible on the blockchain forever, and
unreachable forever.

## Why "recovery services" are how people lose the rest

Every search like the one that brought you here is being watched by people who make their
living from it. If you post about losing access on a forum, in a Telegram group or on social
media, you should expect to be contacted within hours.

The pattern is consistent. Someone presents themselves as a recovery specialist, a wallet
support agent, or a blockchain forensics firm. They are confident. They may show you
testimonials, a professional website, even a case number. What they want is one of two things:
your recovery phrase or partial phrase "so we can run the recovery", or an upfront fee, often
framed as a deposit against funds they will return.

Three rules cover almost all of it. No legitimate party ever needs your recovery phrase, in
whole or in part, for any reason. Anyone who contacts you first, having seen that you are in
trouble, is not helping you. And a phrase that is genuinely lost cannot be brute-forced by
anyone at any price — the search space is larger than the problem is solvable.

The one narrow exception is the partial-phrase case described above, which is a technical
process done offline on your own equipment, not a service you hand your phrase to.

## What to do once you know where you stand

If you have recovered access, treat it as a warning rather than a near miss. Write the phrase
down again, on paper or steel, and then actually test it: restore it onto a second device, or
wipe and restore the hardware wallet, and confirm the same wallet comes back. A backup you
have never tested is an assumption, not a backup — and untested backups are the single most
common way people end up reading pages like this one.

Then store it somewhere that is not with the device, not photographed, not in a notes app, and
not in a cloud backup.

If the funds are genuinely gone, the useful thing left to do is make sure it cannot happen
again with whatever else you hold. In practice, someone who has lost one backup usually has
the same weakness across the rest of their setup: a phrase in one place, never verified, with
no plan for what happens if they are not the one logging in.

## Getting help

KeyCompass is run by Simon Geils, who spent a decade in front-line technical support — first
at Apple, then at a hardware wallet manufacturer, where a great deal of the work was talking
to people on the worst day of their crypto lives. Most of what is on this page comes from
watching the same handful of mistakes repeat.

What KeyCompass does not do is recover lost phrases, and it will never ask you for one. What
it does is check the setup you still have, across the four ways these things fail: phishing,
device compromise, backup loss, and what happens if you are not the one logging in. If you
have just had a fright, that is the useful next step.

There is a free fifteen-minute call to work out whether you need it at all.

- [Book the intake call](https://cal.com/simongeils/15min)
- [hello@keycompass.co.uk](mailto:hello@keycompass.co.uk)

---

KeyCompass provides educational and operational support only. It is not a financial adviser,
is not authorised or regulated by the Financial Conduct Authority, does not provide investment,
legal, or tax advice, and never takes custody of client assets, keys, or recovery phrases.

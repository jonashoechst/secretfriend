Secret Friend
===

Secret Friend is a game for getting to know each other. All participants are pairwise matched without them knowing their counterpart. The objective is to find out your secret friends identity by hints supplied by them.

This implementation is based on the E-Mail system. A participant sends a mail to the secret friend address, which will get forwarded pseudo-anonymously. This is achieved by replacing the `From`, `To` and `Cc` entries according to the configured list of participants.

To enter the game, one writes a mail to the configured address. The software will first send a welcome mail in response and as soon as a secret friend is matched, will inform the user that they can start conversation.

# Setup

`secretfriend.py` is intendet to run in a qmail environment. The secret friend address can be configured using `.qmail` files, e.g.:

```
|./secretfriend/secretfriend.py sf@jonashoechst.de
```

## Sendmail

`secretfriend.py` handles mail transfer via the local sendmail configuration, hence sending mail sendmail should be configured to allow mail sending.

# Usage

```
$ ./secretfriend.py --help
usage: secretfriend.py [-h] [--csv CSV] [-r READ] [-l LOG] [--welcome WELCOME] [--match MATCH] addr

positional arguments:
  addr                  email address for sending mail (should match incoming address)

optional arguments:
  -h, --help            show this help message and exit
  --csv CSV             file to store matched friends
  -r READ, --read READ  file to read message from (default: stdin)
  -l LOG, --log LOG     file to write log messages to (default: messages.log)
  --welcome WELCOME     welcome email
  --match MATCH         match succeeded email
```

## Anonymity

The project is by no means aiming to meet any anonimity goals. Metadata available in the Header, such as `Received`-paths, `Mime-Version`, `Message-Id` or `X-Mailer` can and will be leaked. Mail signatures are not stripped and need to be disabled when playing this game.

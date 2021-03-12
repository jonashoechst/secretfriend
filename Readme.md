Secret Friend
===

Secret Friend is a game for getting to know each other. All participants are pairwise matched without them knowing their counterpart. The objective is to find out your secret friends identity by hints supplied by them.

This implementation is based on the E-Mail system. A participant sends a mail to the secret friend address, which will get forwarded pseudo-anonymously. This is achieved by replacing the `From`, `To` and `Cc` entries according to the configured list of participants.

## Qmail Integration

`secretfriend.py` is intendet to run in a qmail environment. The secret friend address can be configured using `.qmail` files, e.g.:

```
|/home/hoechst7/secretfriend/secretfriend.py sf@jonashoechst.de
```

## Sendmail

`secretfriend.py` handles mail transfer via the local sendmail configuration, hence sendmail should be configured to allow mail sending.

## Anonymity

The project is by no means aiming to meet any anonimity goals. Metadata available in the Header, such as `Received`-paths, `Mime-Version`, `Message-Id` or `X-Mailer` can and will be leaked. Mail signatures are not stripped and need to be disabled when playing this game.

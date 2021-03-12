#!/usr/bin/env python3

from datetime import datetime
from email.message import Message
import email.parser
import email.utils
from io import TextIOWrapper
import os
import sys
from typing import List, Optional
import argparse
import csv
import platform
import fcntl
import logging
import subprocess
from uuid import uuid4

argp = argparse.ArgumentParser()
argp.add_argument("addr", help="email address for sending mail (should match incoming address)")
argp.add_argument("--csv", help="file to store matched friends", default="friends.csv", type=argparse.FileType("a+"))
argp.add_argument("-r", "--read", help="file to read message from (default: stdin)", default=sys.stdin, type=argparse.FileType("r"))
argp.add_argument("-l", "--log", help="file to write log messages to (default: messages.log)", default="messages.log", type=argparse.FileType("a"))
argp.add_argument("--dump-dir", help="dump mails to disk", default=None, type=str)

argp.add_argument("--welcome", help="welcome email", default="welcome.eml", type=argparse.FileType("r"))
argp.add_argument("--match", help="match succeeded email", default="match.eml", type=argparse.FileType("r"))

emlp = email.parser.HeaderParser()


class NewUser(Exception):
    pass


class NewMatch(Exception):
    pass


class UnmatchedUser(Exception):
    pass


def sendmail(msg: Message, dump_dir: Optional[str] = None) -> int:
    # dump mail
    msg_id = msg.get("Message-Id")
    if dump_dir:
        with open(f"{dump_dir}/{msg_id}.eml", "w") as dump:
            dump.write(msg.as_string())

    # send mail
    p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=subprocess.PIPE)
    p.communicate(msg.as_bytes())

    return p.returncode


def fill_template(template: TextIOWrapper, mail_from: str, mail_to: str, reply_msg_id: str) -> Message:
    logging.info(f"Sending {template.name} mail to {mail_to} ({reply_msg_id})")
    template.seek(0, os.SEEK_SET)

    welcome = emlp.parse(template)
    welcome.add_header("To", mail_to)
    welcome.add_header("From", email.utils.formataddr(("Secret Friend", mail_from)))
    welcome.add_header("Date", email.utils.format_datetime(datetime.now()))
    welcome.add_header("Message-Id", f"{uuid4()}@{mail_from.split('@')[1]}")

    welcome.add_header("References", reply_msg_id)
    welcome.add_header("In-Reply-To", reply_msg_id)

    return welcome


def get_friend(csv_file: TextIOWrapper, user: str) -> str:
    # lock friends list file
    csv_file.seek(0, os.SEEK_SET)
    fcntl.flock(csv_file, fcntl.LOCK_SH)

    # read friends list
    friends = dict([(a, b) for a, b in csv.reader(csv_file)])
    friends.update([(b, a) for a, b in friends.items()])

    # if user is already in list
    if user in friends:
        friend = friends[user]
        fcntl.flock(csv_file, fcntl.LOCK_UN)

        # no secret friend is assigned yet
        if friend == "":
            raise UnmatchedUser

        return friend

    fcntl.flock(csv_file, fcntl.LOCK_EX)
    # if there is an unmatched user in the list
    if "" in friends:
        # lookup unmatched friend and update dict
        friend = friends.pop("")
        friends[friend] = user
        friends[user] = friend

        # append user to last line
        csv_file.write(f"{user}\n")

        fcntl.flock(csv_file, fcntl.LOCK_UN)
        raise NewMatch

    # create new line for user
    csv_file.write(f"{user},")
    fcntl.flock(csv_file, fcntl.LOCK_UN)

    raise NewUser


def replace_addrs(addrs: List[str], old: str, new: str) -> str:
    cleaned = []
    for to_name, to_addr in email.utils.getaddresses(addrs):
        if to_addr == old:
            cleaned.append(("", new))
        else:
            cleaned.append((to_name, to_addr))

    return ", ".join([email.utils.formataddr(addr) for addr in cleaned])


def main():
    args = argp.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.dump_dir:
        os.makedirs(args.dump_dir, exist_ok=True)

    # read email
    msg = emlp.parse(args.read)

    # get from address and replace
    from_name, user = email.utils.parseaddr(msg.get("From"))
    msg.replace_header("From", email.utils.formataddr(("Secret Friend", args.addr)))

    # log message in csv format
    csv.writer(args.log).writerow([msg.get("Date"), user, msg.get("Message-Id")])
    logging.info(f"received message {msg.get('Message-Id')} from {user}")

    # try to find friend
    try:
        friend = get_friend(args.csv, user)
        logging.info(f"looked up {friend} for {user}")

    # if new user / new matched user, handle accordingly
    except (NewUser, NewMatch) as e:
        logging.info(f"new user {user}, sending welcome mail")
        sendmail(fill_template(args.welcome, args.addr, user, msg.get("Message-Id")), args.dump_dir)

        if isinstance(e, NewMatch):
            friend = get_friend(args.csv, user)
            logging.info(f"new match {user} / {friend}, sending match mails")
            sendmail(fill_template(args.match, args.addr, user, msg.get("Message-Id")), args.dump_dir)
            sendmail(fill_template(args.match, args.addr, friend, msg.get("Message-Id")), args.dump_dir)

        exit(0)

    # delay message of unmatched friend
    except UnmatchedUser:
        logging.info(f"user {user} does not have a matched friend yet, delay message")
        exit(111)

    # replace secret friend address in To and Cc header fields
    if msg.get("To"):
        msg.replace_header("To", replace_addrs(msg.get_all("To"), args.addr, friend))
    if msg.get("Cc"):
        msg.replace_header("Cc", replace_addrs(msg.get_all("Cc"), args.addr, friend))

    # add secretfriend received header
    msg.add_header("Received", f"(secretfriend.py on {platform.node()}); {email.utils.format_datetime(datetime.now())}")
    exit(sendmail(msg, args.dump_dir))


if __name__ == "__main__":
    main()

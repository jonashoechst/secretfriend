#!/usr/bin/env python3

from datetime import datetime
import email.parser
import email.utils
import sys
from typing import List, Tuple
import argparse
import csv
import platform

argp = argparse.ArgumentParser()
argp.add_argument("addr", help="email address for sending mail (should match incoming address)")
argp.add_argument("csv")
argp.add_argument("-r", "--read", help="file to read message from (default: stdin)", default="-")
argp.add_argument("-w", "--write", help="file to write message to (default: stdout)", default="-")
args = argp.parse_args()

# read email
emlp = email.parser.HeaderParser()
if args.read == "-":
    msg = emlp.parse(sys.stdin)
else:
    with open(args.read) as msg_file:
        msg = emlp.parse(msg_file)

# get from address and replace
from_name, from_addr = email.utils.parseaddr(msg.get("From"))
msg.replace_header("From", email.utils.formataddr(("Secret Friend", args.addr)))

# read friends list
with open(args.csv) as csv_file:
    friends_list: List[Tuple[str, str]] = [(a, b) for a, b in csv.reader(csv_file)]
    friends = dict(friends_list)
    friends.update([(b, a) for a, b in friends_list])

try:
    secretfriend = friends[from_addr]
except KeyError:
    # did not find secret friend, abort submission
    exit(100)


def replace_secretfriend(addrs: List[str]) -> str:
    cleaned = []
    for to_name, to_addr in email.utils.getaddresses(addrs):
        if to_addr == args.addr:
            cleaned.append(("", secretfriend))
        else:
            cleaned.append((to_name, to_addr))

    return ", ".join([email.utils.formataddr(addr) for addr in cleaned])


# replace secret friend address in To and Cc header fields
to = msg.get_all("To")
if to:
    msg.replace_header("To", replace_secretfriend(to))

cc = msg.get_all("Cc")
if cc:
    msg.replace_header("Cc", replace_secretfriend(cc))

msg_string = f"Received: (secretfriend.py on {platform.node()}); {email.utils.format_datetime(datetime.now())}\n"
msg_string = msg.as_string()

if args.write == "-":
    sys.stdout.write(msg_string)
else:
    with open(args.write, "w") as out:
        out.write(msg_string)

# write message metadata to log
with open("secretfriend_log.csv", "a") as log:
    writer = csv.writer(log)
    writer.writerow([msg.get("Date"), from_addr, secretfriend, msg.get("Subject")])

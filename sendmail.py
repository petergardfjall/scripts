#!/usr/bin/env python3

#
# Email sending client.
#

import argparse
import getpass
import logging
import smtplib
import sys

# Import the email modules we'll need
from email.mime.text import MIMEText


LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s [%(levelname)s] %(message)s"),
    stream=sys.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fromaddr", default=None, type=str,
                        help=("From: mail header. If none is given, user will be prompted."))
    parser.add_argument("--subject", default=None, type=str,
                        help=("Subject: mail header. If none is given, user will be prompted."))
    parser.add_argument("--message-file", metavar="FILE", default=None,
                        type=str,
                        help=("File with message content. If none is given, user will be prompted."))
    parser.add_argument("--username", default=None, type=str,
                        help=("User name used to authenticate. If none is given, user will be prompted."))
    parser.add_argument("--password", default=None, type=str,
                        help=("Password used to authenticate. If none is given, user will be prompted."))
    parser.add_argument("--smtp-host", default="localhost", type=str,
                        help=("SMTP server hostname or IP address."))
    parser.add_argument("--smtp-port", default=587, type=int,
                        help=("SMTP port. Typically one of 25, 465 (SSL), 587 (STARTTLS)."))
    parser.add_argument("--smtp-debuglevel", default=0, type=int,
                        help=("smtplib debug level. Default: 0."))
    parser.add_argument("--use-ssl", action="store_true", default=False,
                        help=("Forces the use of SSL on the connection. "
                              "Should typically be used when connecting "
                              "to port 465."))
    parser.add_argument("toaddr", metavar="<To address>", type=str, help="Email receiver. To: address.")
    args = parser.parse_args()


    if not args.username:
        args.username = input("SMTP username: ")
    if not args.password:
        args.password = getpass.getpass("SMTP password: ")
    if not args.fromaddr:
        args.fromaddr = input("From: ")
    if not args.subject:
        args.subject = input("Subject: ")

    args.lines = []
    if args.message_file:
        with open(args.message_file, "r") as stdin:
            args.lines = stdin.readlines()
    else:
        print("Message (Ctrl-d to end): ")
        for line in sys.stdin:
            args.lines.append(line)

    msg = MIMEText("".join(args.lines))
    msg['Subject'] = args.subject
    msg['From'] = args.fromaddr
    msg['To'] = args.toaddr


    if args.use_ssl:
        mailserver = smtplib.SMTP_SSL()
    else:
        mailserver = smtplib.SMTP()

    mailserver.set_debuglevel(args.smtp_debuglevel)
    LOG.info("connecting to %s:%d ...", args.smtp_host, args.smtp_port)
    mailserver.connect(args.smtp_host, args.smtp_port)
    LOG.info("connected.")

    try:
        ehlo_response = mailserver.ehlo()
        LOG.debug("ehlo response: %s", ehlo_response)
        if mailserver.has_extn("STARTTLS"):
            LOG.info("Switching to TLS, server appears STARTTLS-capable.")
            mailserver.starttls()
        mailserver.login(args.username, args.password)
        LOG.info("logged in.")
        LOG.info("sending email ...")
        mailserver.sendmail(args.fromaddr, [args.toaddr], msg.as_string())
        LOG.info("email sent.")
    finally:
        mailserver.quit()

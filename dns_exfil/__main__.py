#!/usr/bin/env python3
import argparse
import json
import socketserver
import sys
from typing import Tuple

from dnslib import DNSRecord
from dnslib.server import BaseResolver


class DNSLoggerHelper:
    """Helper for DNSLogger"""

    @staticmethod
    def parse_suffix(suffix: str) -> str:
        """Parse a suffix string. If suffix does not start and end with a ".", make it do so.

        Example:
            "evil.com" -> ".evil.com."

        Args:
            suffix (str): [description]

        Returns:
            str: [description]
        """
        if not suffix:
            return suffix
        return "." + suffix.strip(".") + "."

    @staticmethod
    def gracefully_decode_hex(data: str) -> str:
        """Gracefully decode hex within data string. Graceful in that a non-hex-encoded data string will be returned as-is.

        Args:
            data (str): the hex string to decode

        Returns:
            str: the decoded hex value of data
        """
        try:
            data = bytes.fromhex(data).decode("utf-8")
        except ValueError:
            pass
        return data

    @staticmethod
    def remove_suffix(data: str, suffix: str) -> str:
        """Remove suffix from string

        Args:
            data (str): the input data to remove suffix from
            suffix (str): the suffix to remove

        Returns:
            str: the data string without the suffix
        """
        if suffix and data.endswith(suffix):
            data = data[: -len(suffix)]
        return data

    @staticmethod
    def parse_sender(sender: Tuple[str, int]) -> str:
        """Turn a sender tuple into a ip:port string

        Args:
            sender (Tuple[str, int]): sender ip and port tuple

        Returns:
            str: the sender ip and port join
        """
        return f"{sender[0]}:{sender[1]}"


class DNSLogger:
    """Logger for DNS queries"""

    def __init__(self, hex_encoded: bool = False, suffix: str = "") -> None:
        self.hex_encoded = hex_encoded
        self.suffix = DNSLoggerHelper.parse_suffix(suffix)

    def parse_question(self, question: str) -> str:
        """Parse a DNSRecord question by decoding hex if portion after suffix is supposed to be hex-encoded. In case it is not hex-encoded, the parsing is still graceful (doesn't change anything).

        Example:
            "68656c6c6f20776f726c640a.suffix.com" -> "hello world.suffix.com"

        Args:
            question (str): a DNSRecord's question

        Returns:
            str: the parsed question
        """
        if not self.hex_encoded:
            return question
        # Remove FQDN suffix
        unsuffixed_question = DNSLoggerHelper.remove_suffix(question, self.suffix)
        # Parse hex of each subdomain
        decoded_subdomains = map(
            DNSLoggerHelper.gracefully_decode_hex, unsuffixed_question.split(".")
        )
        # Re-join subdomains and suffix (if question started with it originally)
        result = ".".join(decoded_subdomains)
        if question.endswith(self.suffix):
            result += self.suffix
        return result

    def log(self, sender: Tuple[str, int], record: DNSRecord) -> None:
        """Log a DNS request

        Args:
            sender (Tuple[str, int]): the sender's IP address
            request_data (DNSRecord): the raw, un-parsed request data (from socketserver)
        """
        question = record.get_q()
        qname_str = str(question.get_qname())
        parsed_qname_str = self.parse_question(qname_str)
        result = {
            "sender": DNSLoggerHelper.parse_sender(sender),
            "raw_question": str(question),
            "parsed_qname": parsed_qname_str,
        }
        print(json.dumps(result, indent=4), flush=True)


class DNSHandler(socketserver.BaseRequestHandler):
    """A custom socketserver request handler for handling our DNS queries (to be passed into a socketserver server)"""

    def handle(self) -> None:
        data, connection = self.request
        parsed_record = DNSRecord.parse(data)
        self.server.logger.log(self.client_address, parsed_record)  # type: ignore
        response = self.server.resolver.resolve(parsed_record, self)  # type: ignore
        connection.sendto(response.pack(), self.client_address)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


def main():
    # Parse args
    argparser = argparse.ArgumentParser(
        description="Open a DNS server that knows no records but records every request. Used for DNS exfiltration."
    )
    argparser.add_argument(
        "-a",
        "--address",
        dest="host",
        action="store",
        metavar="HOST",
        type=str,
        help="Server host (default: 127.0.0.1)",
        default="127.0.0.1",
    )
    argparser.add_argument(
        "-p",
        "--port",
        dest="port",
        action="store",
        metavar="PORT",
        type=int,
        help="Server port (default: 53)",
        default=53,
    )
    argparser.add_argument(
        "-he",
        "--hex-encoded",
        dest="hex_encoded",
        action="store_true",
        help="Enable hex decoding",
    )
    argparser.add_argument(
        "-s",
        "--suffix",
        dest="suffix",
        action="store",
        type=str,
        help="Default FQDN suffix of DNS questions (recommended when DNS requests are hex encoded); example: '.evil.com.'",
        default="",
    )
    args = argparser.parse_args()
    # Create server
    try:
        server = ThreadedUDPServer((args.host, args.port), DNSHandler)
    except PermissionError:
        sys.exit(
            "Error: couldn't create DNS server due to a permission issue. Try running with sudo."
        )
    server.resolver = BaseResolver()
    server.logger = DNSLogger(args.hex_encoded, args.suffix)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import socketserver
from copy import deepcopy

from dnslib import DNSRecord
from dnslib.server import BaseResolver


class DNSLoggerHelper:
    @staticmethod
    def parse_suffix(suffix):
        if not suffix:
            return suffix
        return "." + suffix.strip(".") + "."

    @staticmethod
    def decode_hex(data):
        try:
            data = bytes.fromhex(data).decode("utf-8")
        except ValueError:
            pass
        return data

    @staticmethod
    def remove_suffix(data, suffix):
        if suffix and data.endswith(suffix):
            data = data[: -len(suffix)]
        return data


class DNSLogger:
    def __init__(self, hex_encoded=False, suffix=""):
        self.hex_encoded = hex_encoded
        self.suffix = DNSLoggerHelper.parse_suffix(suffix)

    def parse_question(self, question):
        if not self.hex_encoded:
            return question

        qname = str(question.get_qname())
        suffixed = DNSLoggerHelper.remove_suffix(qname, self.suffix)
        decoded_subdomains = map(DNSLoggerHelper.decode_hex, suffixed.split("."))
        question.set_qname(".".join(decoded_subdomains) + self.suffix)
        return question

    def log(self, sender, parsed_req):
        original_q = str(parsed_req.get_q().get_qname())
        question = self.parse_question(parsed_req.get_q())
        print(f"{sender}: {question} ({original_q})")


class DNSHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, connection = self.request
        parsed_req = DNSRecord.parse(data)
        # (deep copying parsed_req as to not change our coming DNS response)
        self.server.logger.log(self.client_address, deepcopy(parsed_req))
        response = self.server.resolver.resolve(parsed_req, self)
        connection.sendto(response.pack(), self.client_address)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


def main():
    # Parse args
    argparser = argparse.ArgumentParser(
        description="Open a DNS server that knows no records, but does record every request."
    )
    argparser.add_argument(
        "-a",
        "--address",
        dest="host",
        action="store",
        metavar="HOST",
        type=str,
        default="127.0.0.1",
    )
    argparser.add_argument(
        "-p",
        "--port",
        dest="port",
        action="store",
        metavar="PORT",
        type=int,
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
        help="Default FQDN suffix of DNS questions (should use when DNS requests are hex encoded)",
        default="",
    )
    args = argparser.parse_args()
    # Create server
    server = ThreadedUDPServer((args.host, args.port), DNSHandler)
    server.resolver = BaseResolver()
    server.logger = DNSLogger(args.hex_encoded, args.suffix)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

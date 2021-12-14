# dns-exfil

Run a DNS server for the purpose of logging DNS questions. Can be used for DNS exfiltration or for good-old DNS pingback detection.

![dns-exfil example run](misc/dns-exfil-display.png)


## Usage

```
$ dns-exfil --help
usage: dns-exfil [-h] [-a HOST] [-p PORT] [-he] [-s SUFFIX]

Open a DNS server that knows no records but records every request. Used for DNS exfiltration.

optional arguments:
  -h, --help            show this help message and exit
  -a HOST, --address HOST
                        Server host (default: 127.0.0.1)
  -p PORT, --port PORT  Server port (default: 53)
  -he, --hex-encoded    Enable hex decoding
  -s SUFFIX, --suffix SUFFIX
                        Default FQDN suffix of DNS questions (recommended when DNS requests are hex encoded); example: '.evil.com.'
```

## How to install

```
$ git clone https://github.com/KarimPwnz/dns-exfil.git
$ cd dns-exfil
$ python3 setup.py install
```

## DNS pingback set-up

1. Start your DNS server by running `dns-exfil`

2. Set-up the server as the `NS` for a domain

   ![DNS NS setup on Cloudflare](misc/dns-NS-setup.png)

3. Send your target to `<whatever_you_want>.dns_exfil_domain`

## DNS exfiltration set-up

Same setup as for DNS pingback. To exfiltrate data through DNS, you'll probably want dns-exfil to decode hex-encoded data. You can enable that feature by passing the `--hex-encoded` (`-he`) flag into dns-exfil; for more accurate parsing, specify the FQDN of your DNS exfiltration domain through the `--suffix` (`-s`) flag. Example: `dns-exfil -he -s '.dnspwn.karimrahal.com.'`. In case the DNS question does not contain hex encoded values, dns-exfil will still parse it correctly.

## Output

The output is in JSONL format:

```json
{
    "timestamp": "2021-12-14 11:10:51.345230",
    "sender": "127.0.0.1:59482",
    "raw_question": ";73656372657431333337.dnspwn.karimrahal.com. IN      A",
    "parsed_qname": "secret1337.dnspwn.karimrahal.com."
}
{
    "timestamp": "2021-12-14 11:11:04.232967",
    "sender": "127.0.0.1:49211",
    "raw_question": ";hello.world.dnspwn.karimrahal.com. IN      A",
    "parsed_qname": "hello.world.dnspwn.karimrahal.com."
}
```

## Showing only parsed qname

```
$ dns-exfil | jq -r '.parsed_qname'
```


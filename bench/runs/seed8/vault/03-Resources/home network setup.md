# home network setup

## topology

ISP modem (bridge mode) -> router -> 8-port managed switch -> everything wired. One AP in the hallway, wired back to the switch. Router does routing/firewall/DHCP only, its built-in wifi is OFF.

- modem is in bridge mode so no double NAT. if internet is weird after an ISP visit, check this first, they sometimes reset it
- NAS + desktop on switch ports 1-2, AP on port 8 (PoE)
- patch panel in the closet, labels fading, redo them

## vlans / subnets

- 10 = trusted (laptops, phone, desktop) 192.168.10.0/24
- 20 = iot (cameras, plugs, tv, robot vacuum) 192.168.20.0/24
- 30 = guest, internet only, client isolation on
- 99 = mgmt (switch, AP, router admin UI)

iot can't initiate to trusted. trusted can reach iot. mDNS reflector enabled between 10 and 20 or casting breaks. Printer lives on 10, annoying but easier than fighting it.

## wifi

- 3 SSIDs mapped to vlans 10/20/30
- iot SSID is 2.4GHz only, otherwise half the plugs refuse to pair
- trusted SSID: wpa3 transitional, 5GHz + 6GHz, channel width 80
- 5GHz channel fixed to 44 after auto kept hopping and dropping calls
- guest password rotates every few months, QR code taped inside the cabinet

## dns

- local resolver on the NAS (container) with blocklists, upstream over DoT
- router DHCP hands out NAS as DNS, with a fallback to 1.1.1.1 on a secondary
- if the NAS is down, everything still resolves via the fallback, just no filtering
- static leases for: NAS (.10), AP, switch, printer. everything else dynamic
- local names like nas.home.lan live in the resolver config, not /etc/hosts

## remote access

- wireguard on the router, one peer per device, no shared keys
- only UDP port forwarded, nothing else exposed
- full tunnel on phone when on public wifi, split tunnel on laptop
- DDNS hostname updates from the router, check it if the tunnel stops connecting after a power cut

## backups / maintenance

- router config export after any change, stored on NAS and an offline copy
- switch config saved to flash, export too (easy to forget)
- firmware updates: AP and router quarterly, not on a Friday
- UPS covers modem, router, switch, NAS. about 20 min runtime

## troubleshooting order

1. is the modem in bridge mode / does it have a WAN IP
2. router can ping 1.1.1.1 but clients can't resolve -> DNS (NAS container)
3. one vlan broken -> check trunk port tagging on the switch
4. wifi flaky -> channel, then AP uplink negotiation (should be 1G)
5. last resort: reboot in order modem, router, switch, AP

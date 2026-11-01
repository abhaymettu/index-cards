# home network setup

## layout
- ISP modem in bridge mode, so it does nothing but pass the connection through
- router behind it is the real gateway, runs DHCP + DNS forwarding
- one managed switch in the office, unmanaged 5-port in the living room for TV/console
- 2 APs, wired backhaul, both on the same SSIDs so roaming works
- main subnet 192.168.1.0/24, IoT on its own VLAN (192.168.30.0/24), guest on 192.168.40.0/24

## addressing
- DHCP pool .100-.199, everything below .100 is static or reserved
- .1 router, .2 switch, .3 and .4 APs
- .10 NAS, .11 pi (dns + misc services)
- reserve by MAC in router instead of setting static on the device, easier to change later
- keep a printout of the reservations table, last time the router reset I had to rebuild from memory

## wifi
- 5GHz SSID for laptops/phones, separate 2.4GHz-only SSID for IoT junk (plugs, cameras, sensors)
- IoT VLAN can reach internet but not the main LAN, only exception is the rule letting HA talk to the plugs
- guest net is isolated, client isolation on, bandwidth capped at ~30mbps
- channels: 36 and 149 for the APs, 1 and 11 on 2.4. don't use auto, it kept flapping

## dns
- pi runs a DNS sinkhole with upstream set to encrypted DoH resolver
- router hands out pi as primary DNS, secondary is the router itself as a fallback (leaks queries around the blocker but better than no internet when pi is down)
- local names like nas.home.lan live in the pi's local records

## remote access
- wireguard on the router, one port forwarded, UDP only
- split tunnel, only routes 192.168.1.0/24 and the pi
- keys per device, revoke by deleting the peer, don't reuse

## gotchas
- if wifi is slow, check the AP uplink negotiated 1Gb, a bad cable dropped one to 100Mb once
- firmware updates on the router: take a config backup first, always
- UPS covers modem, router, switch, NAS. APs are PoE from the switch so they stay up too
- reboot order after a power cut: modem, router, switch, then pi and NAS

## todo
- label the patch panel properly
- set up scheduled config backup to the NAS
- check if the switch supports mirroring for debugging

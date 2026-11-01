# home network setup

## hardware
- ISP modem in bridge mode, so it only passes the public IP through and does no NAT
- router: small x86 box running OPNsense, 4x 2.5G ports. WAN on port 1, LAN trunk on port 2
- main switch: 16-port managed, sits in the hall closet. Uplink to the router is a trunk with all VLANs tagged
- 2 APs, both PoE-powered from the switch. Wired backhaul, no mesh. Channels set by hand (1 and 11 on 2.4, 36 and 149 on 5)
- NAS in the closet, bonded 2x1G to the switch (LACP). Honestly overkill

## vlans / subnets
- 10 = trusted (laptops, phone) → 10.0.10.0/24
- 20 = IoT (cameras, bulbs, TV, vacuum) → 10.0.20.0/24
- 30 = guest → 10.0.30.0/24, internet only, client isolation on
- 99 = management (switch, APs, router UI) → 10.0.99.0/24
- IoT can't initiate to trusted. Trusted can reach IoT. Return traffic allowed via state
- cameras have no WAN access at all, only to the NAS for recording

## dhcp / dns
- DHCP static leases for anything I need to find: NAS = .10, printer = .20, switch = .2, APs = .3 and .4
- DNS: router runs Unbound, forwards to a local resolver w/ blocklists, upstream over DoT
- split DNS override so `nas.home.lan` resolves internally even when the VPN is up
- block outbound port 53 from IoT unless it's to the router (some TVs hardcode 8.8.8.8, annoying)

## remote access
- WireGuard on the router, one peer per device, UDP 51820 forwarded
- full tunnel on phone, split tunnel on laptop (only 10.0.0.0/16)
- DDNS updates every 5 min from the router, check this first if the VPN suddenly dies

## backups / config
- OPNsense config exported weekly to the NAS, plus a copy offsite
- switch config backed up manually after any change. Easy to forget!
- keep a printed sheet in the closet with the admin IPs and the recovery steps

## gotchas
- mDNS doesn't cross VLANs, so casting/AirPlay needs the mDNS repeater enabled on 10 and 20
- after changing the trunk's VLAN list, reboot the APs or the SSIDs sometimes don't come back
- the modem resets to routing mode after a power cut about 1 time in 10. Check bridge mode if the WAN has a private IP
- don't touch the management VLAN from wifi; keep a wired port on 99 as a fallback

## todo
- put the closet on a UPS
- try 802.1X on the trusted SSID
- label the patch panel properly

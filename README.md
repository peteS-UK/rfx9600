# Home Assistant to Philips RFX9600 Relays

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)


This custom component implements a device and 4 switch entities for Home Assistant to allow for control of the relays .  

The integration is a Local Polling integration but polling is only every 240 seconds, since the device state being changed frequently outside of Home Assistant seems unlikely.

## Installation

The preferred installation approach is via Home Assistant Community Store - aka [HACS](https://hacs.xyz/).  The repo is installable as a [Custom Repo](https://hacs.xyz/docs/faq/custom_repositories) via HACS.

If you want to download the integration manually, create a new folder called rfx9600 under your custom_components folder in your config folder.  If the custom_components folder doesn't exist, create it first.  Once created, download the files and folders from the [github repo](https://github.com/peteS-UK/rfx9600/tree/main/custom_components/rfx9600) into this new rfx9600 folder.

Once downloaded either via HACS or manually, restart your Home Assistant server.

## Configuration

Configuration is done through the Home Assistant UI.  Once you're installed the integration, go into your Integrations (under Settings, Devices & Services), select Add Integration, and choose the Philips RFX9600 integration.

This will display the configuration page, where you can select the IP address and name of the RFX.  You can also optionally name the relays, or leave them as their default values.

## RS232 service

The integration now exposes an action/service `rfx9600.send_rs232` to send serial commands over the RFX9600.

Service data:

- `port` (required): RS232 port number (`1`-`4`)
- `command` (required): ASCII command string to send
- `baud_rate` (required): one of `2400`, `4800`, `9600`, `14400`, `19200`, `28800`, `31250`, `38400`, `57600`, `115200`
- `stop_bits` (required): `1`, `1.5`, or `2`
- `parity` (required): `none`, `even`, `odd`, `mark`, or `space`
- `data_bits` (required): `5`, `6`, `7`, or `8`
- `duration_ms` (optional, default `500`)
- `repeat_count` (optional, default `1`)

Example:

```yaml
action: rfx9600.send_rs232
data:
  port: 1
  command: "PWR ON\r"
  baud_rate: 9600
  stop_bits: 1
  parity: none
  data_bits: 8
```

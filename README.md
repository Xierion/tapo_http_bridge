# Tapo P100 HTTP bridge for Moonraker

Moonraker has no built-in Tapo support, but its `power` component supports
a generic `type: http` device that hits arbitrary URLs. This bridge is a
small Flask server that translates those requests into calls against the
[almottier/TapoP100](https://github.com/almottier/TapoP100) (`PyP100`)
library.

## 1: Update System and Install Dependencies
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3
```

## 2. Clone the repository

Clone Tapo P100 HTTP bridge
```bash
cd ~
git clone https://github.com/Xierion/tapo_http_bridge.git
cd ~/tapo_http_bridge
```
## 3. Create a venv and install deps

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

## 4. Configure your plug + Tapo account

```bash
cp config.example.json config.json
nano config.json      # fill in ip, email, password
chmod 600 config.json # it's plaintext, so lock it down
```

`ip` is the plug's local IP (give it a DHCP reservation on your router so
it doesn't move). `email`/`password` are your TP-Link/Tapo **account**
credentials (the ones you use in the Tapo app, both case-sensitive), not a device password.

## 5. Quick manual test (before installing the service)

```bash
source venv/bin/activate
python3 app.py
```

In another terminal:

```bash
curl http://127.0.0.1:5111/status
curl http://127.0.0.1:5111/on
curl http://127.0.0.1:5111/off
```

You should get back `{"status": "on"}` / `{"status": "off"}`. Ctrl-C the
server once this works.

## 6. Install as a systemd service

```bash
sudo cp tapo-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tapo-bridge.service
sudo systemctl status tapo-bridge.service
```

Logs: `journalctl -u tapo-bridge.service -f`

## 7. Add it to moonraker.conf

Append to `~/printer_data/config/moonraker.conf` (adjust the section name
`[power tapo_plug]` to whatever you want it called in Mainsail/Fluidd):

```ini
[power tapo_plug]
type: http
on_url: http://127.0.0.1:5111/on
off_url: http://127.0.0.1:5111/off
status_url: http://127.0.0.1:5111/status
response_template:
    {% set resp = http_request.last_response().json() %}
    {resp["status"]}
locked_while_printing: True
off_when_shutdown: False # Set to True to power off on M112 emergency stop
```

Then restart Moonraker:

```bash
sudo systemctl restart moonraker
```

You should now see a power toggle for `tapo_plug` in Mainsail/Fluidd.

## Notes

- The bridge only listens on `127.0.0.1`, since Moonraker runs on the same
  Pi and the config file contains your Tapo account password. Don't expose
  port 5111 externally. This can be changed by modifying app.py
- Requests to the plug are serialized with a lock, since the Tapo protocol
  doesn't handle concurrent sessions well.
- If `pip install` for `PyP100` fails, make sure `git` is installed
  (`sudo apt install git`) since it's installed directly from GitHub.
- Use code in printer.cfg to enable idle poweroff

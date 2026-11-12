#!/usr/bin/env python3
"""Export a secret-free Tasmota profile for the Panda Stella A mod.

Reads the running device over its local web API and writes:
  tasmota/profile.json                 - settings snapshot
  tasmota/panda-stella.template.json   - importable Tasmota template

The full backup (Backup Configuration / /dl) is intentionally NOT written here:
it contains Wi-Fi credentials and must stay out of the repo.
"""

import datetime
import json
import urllib.parse
import urllib.request

BASE = "http://pandastella.lan"
ORDER = ["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO9",
         "GPIO10", "GPIO12", "GPIO13", "GPIO14", "GPIO15", "GPIO16", "GPIO17"]


def api(cmnd):
    url = f"{BASE}/cm?cmnd={urllib.parse.quote(cmnd)}"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)


def main():
    status = api("Status 0")
    gpio = api("Gpio")

    pins = {}
    for pin, variants in gpio.items():
        fid, name = next(iter(variants.items()))
        pins[pin] = {"id": int(fid), "function": name}

    profile = {
        "exported": datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds"),
        "source": BASE + "/",
        "device": {
            "hostname": status["StatusNET"]["Hostname"],
            "ip": status["StatusNET"]["IPAddress"],
            "mac": status["StatusNET"]["Mac"],
            "hardware": status["StatusFWR"]["Hardware"],
            "firmware": status["StatusFWR"]["Version"],
            "build": status["StatusFWR"]["BuildDateTime"],
        },
        "module": {"id": status["Status"]["Module"], "name": "Generic", "base": 18},
        "gpio": {
            pin: pins[pin]
            for pin in sorted(pins, key=lambda p: int(p[4:]))
        },
        "channels": {
            "power": len(status["Status"]["Power"]),
            "dimmer": True,
            "counter": True,
        },
        "settings": {
            "friendly_names": status["Status"]["FriendlyName"],
            "topic": status["Status"]["Topic"],
            "power_on_state": status["Status"]["PowerOnState"],
            "serial": {
                "baudrate": status["StatusPRM"]["Baudrate"],
                "config": status["StatusPRM"]["SerialConfig"],
            },
            "timezone": status["StatusTIM"]["Timezone"],
            "wifi_config": status["StatusNET"]["WifiConfig"],
        },
    }

    template_gpio = [1] * len(ORDER)
    for i, pin in enumerate(ORDER):
        if pin in profile["gpio"]:
            template_gpio[i] = profile["gpio"][pin]["id"]

    template = {"NAME": "PandaStella", "GPIO": template_gpio, "FLAG": 0, "BASE": 18}

    with open("tasmota/profile.json", "w") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open("tasmota/panda-stella.template.json", "w") as f:
        json.dump(template, f, indent=2)
        f.write("\n")

    print(json.dumps(template))
    print(json.dumps(profile, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

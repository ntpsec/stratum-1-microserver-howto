#!/usr/bin/env python
#
# Configure an SBC as a single-purpose timeserver.
#
# To run this, you must have created a non-root, non-default account
# on the SBC. Copy it to the account's $HOME, go root there, and
# run it.
#
# If there is a local config utility such as raspi-config on the
# Raspberry Pi, you should already have run it before this.
#
# The evironment is assumed to be Debian Linux variant.
#
import sys, os, re

try:
    my_input = raw_input
except NameError:
    my_input = input

# If this changes, the corresponding Makefile declrationm must as well.
webfaq = "http://www.catb.org/esr/faqs/stratum-1-microserver-howto/"

# Map hardware revision numbers to Raspeberry Pi versions
version_dict = {
    "0002" : "Model B Revision 1.0",
    "0003" : "Model B Revision 1.0",
    "0004" : "Model B Revision 2.0",
    "0005" : "Model B Revision 2.0",
    "0006" : "Model B Revision 2.0",
    "0007" : "Model A",
    "0008" : "Model A",
    "0009" : "Model A",
    "000d" : "Model B Revision 2.0",
    "000e" : "Model B Revision 2.0",
    "000f" : "Model B Revision 2.0",
    "0010" : "Model B+",
    "0011" : "Compute Module",
    "0012" : "Model A+",
    "a01041" : "Pi 2 Model B",
    "a21041" : "Pi 2 Model B",
    "900092" : "PiZero",
    "a02082" : "Pi 3 Model B",
    "a22082" : "Pi 3 Model B",
}

def config():
    "Perform root-mode preconfiguration of the SBC"
    if os.path.exists("/dev/ttyAMA0"):
        sbc_type = "RPi"
        default_login = "pi"
        print("This is a Raspberry Pi")
    else:
        print("Unknown SBC type.")
        raise SystemExit(1)

    if os.geteuid() != 0:
        print("This functiopm must run as root.")
        raise SystemExit(0)

    # Determine the Pi version
    revno = None
    for line in open("/proc/cpuinfo"):
        if line.startswith("Revision"):
            revno = line.split()[2]
    if revno is None or revno not in version_dict:
        print("Can't identify SBC version")
        raise SystemExit(0)
    else:
        print("I see hardware revision %s, %s" % (revno, version_dict[revno]))

    print("")

    reboot_required = False

    if ("\n"+ default_login + ":") in open("/etc/passwd").read():
        print("Default login is still present.")
        os.system("deluser %s" % default_login)
        reboot_required = True
    else:
        print("Default login has been removed.")

    rp = open("/etc/ssh/sshd_config", "r")
    wp = open("/etc/ssh/sshd_config-new", "w")
    modified = False
    for line in rp:
        if line.startswith("PermitRootLogin") and "no" not in line:
            modified = True
            line = "PermitRootLogin no\n"
        elif line.startswith("#PermitRootLogin"):
            modified = True
            line = "PermitRootLogin no\n"
        elif line.startswith("PasswordAuthentication") and "no" not in line:
            modified = True
            line = "PasswordAuthentication no\n"
        elif line.startswith("#PasswordAuthentication"):
            modified = True
            line = "PasswordAuthentication no\n"
        wp.write(line)
    if modified:
        print("Disabling root login and password tunneling.")
        os.rename("/etc/ssh/sshd_config-new", "/etc/ssh/sshd_config")
        reboot_required = True
    else:
        print("Root login and password tunneling are already disabled.")

    print("")

    print("About to upgrade your OS")
    os.system("apt-get update; apt-get dist-upgrade")

    print("")

    if sbc_type == "RPi" and "3" in version_dict[revno]:
        # This should only be done conditionally, on a 
        bc = "/boot/config.txt"
        rp3_overlay = """
# Disable Bluetooth so serial-tty speed is no longer tied to CPU speed
dtoverlay=pi3-miniuart-bt-overlay
"""
    if "dtoverlay=pi3-miniuart-bt-overlay" in open(bc).read():
        print("Bluetooth use of UART already disabled.")
    else:
        print("Reclaiming serial UART.")
        with open(bc, "a") as ap:
            ap.write(rp3_overlay)
        reboot_required = True

    print("")
    if sbc_type == "RPi":
        bc = "/boot/config.txt"
        gpio_re = re.compile("dtoverlay=pps-gpio,gpiopin=([0-9]*)")
        m = gpio_re.search(open(bc).read())
        if m:
            print("GPIO pin already configured to %s." % m.group(1))
        else:
            print("Configuring GPIO pin....")
            #   GPIO04      |      P1-7     | Adafruit
            #   GPIO18      |      P1-12    | Uputronics
            #   GPIO05      |      PI-29    | SKU 424254
            pin_dict = {
                "Adafruit HAT" : 4,
                "Uputronics HAT" : 12,
                "SKU 42425" : 5,
                }
            while True:
                pin = None
                for k in pin_dict:
                    print("%s = %s" % (k[0], k))
                sel = my_input("Select a GPS daughterboard type: ").upper()
                for k in pin_dict:
                    if k.startswith(sel):
                        pin = pin_dict[k]
                if pin is not None:
                    print("Configuring for PPS via GPIO pin %s" % pin)
                    break
            gpio = """
# Get 1PPS from HAT pin 
dtoverlay=pps-gpio,gpiopin=%s
"""
            with open(bc, "a") as ap:
                ap.write(gpio % pin)
            reboot_required = True

        print("")

        print("Getting build and test prerequisites")
        prerequisites = "apt-get install pps-tools git scons ncurses-dev "\
                        "python-dev bc bison libevent-dev libreadline-dev "\
                        "libcap-dev libssl-dev"
        os.system(prerequisites)

        print("")
        if reboot_required:
            print("A reboot is rquired for configuration changes to take effect")
            os.system("reboot")
        else:
            print("No configuration changes - no reboot is required.")

def build():
    "Perform fetch and build of the software."
    if os.geteuid() == 0:
        print("This function should not run as root.")
        raise SystemExit(0)

    builds = 0

    if not os.path.isdir("gpsd"):
        os.system("git clone git://git.savannah.nongnu.org/gpsd.git")
        os.chdir("gpsd")
        os.system("scons timeservice=yes mtk3301=yes fixed_port_speed=9600 fixed_stop_bits=1")
        os.chdir("..")
        builds += 1

    if not os.path.isdir("ntpsec"):
        os.system("git clone https://gitlab.com/NTPsec/ntpsec.git")
        os.chdir("ntpsec")
        os.system("./waf configure --refclock=28")
        os.system("./waf build")
        os.chdir("..")
        builds += 1

    localconf = """\
# /etc/ntp.conf, configuration for ntpd; see ntp.conf(5) for help

# GPS Serial data reference (NTP0)
server 127.127.28.0
fudge 127.127.28.0 refid GPS

# GPS PPS reference (NTP1)
server 127.127.28.1 time2 0.0 prefer
fudge 127.127.28.1 refid PPS

# Internet time servers
server 0.pool.ntp.org iburst noselect
server 1.pool.ntp.org iburst noselect
server 2.pool.ntp.org iburst noselect
server 3.pool.ntp.org iburst noselect

# By default, exchange time with everybody, but don't allow configuration.
restrict default kod nomodify notrap nopeer noquery  
restrict -6 default kod nomodify notrap nopeer noquery

# Local users may interrogate the ntp server more closely.
restrict 127.0.0.1  
restrict -6 ::1

# Drift file etc.
driftfile /var/lib/ntp/ntp.drift
"""
    if not os.path.exists("ntp.conf"):
        os.system("wget %s/ntp.conf" % webfaq)
        builds += 1

    if builds == 0:
        print("All components are built.")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("--config", "--build"):
        print("Please specify a configueration stage argument:")
        print("  --config = basic SBC configuration")
        print("  --build = build timeserver software")
        raise SystemExit(1)

    if sys.argv[1] == "--config":
        config()
    if sys.argv[1] == "--build":
        build()


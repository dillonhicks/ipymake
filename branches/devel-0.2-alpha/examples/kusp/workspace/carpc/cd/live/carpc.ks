# Maintained by the Fedora Desktop SIG:
# http://fedoraproject.org/wiki/SIGs/Desktop
# mailto:fedora-desktop-list@redhat.com

%include carpc-base.ks

%packages
#@games
@graphical-internet
#@graphics
@sound-and-video
@gnome-desktop
nss-mdns
-NetworkManager-vpnc
-NetworkManager-openvpn
# we don't include @office so that we don't get OOo.  but some nice bits
abiword
#gnumeric
#planner
#inkscape

# email
thunderbird
# gps
gpsdrive
PyQt4
pygame
dmode
mplayer
mplayer-gui
# Ack gvfs-fuse is creating a corrupt directory
-gnome-mplayer
-gvfs-fuse

############## Default Fedora live cd settings #########
# avoid weird case where we pull in more festival stuff than we need
# Text to speech support
-gnome-speech
-festival
-festvox-slt-arctic-hts
# Onscreen keyboard but I can't get it to work right.
# It also pulls in the speech stuff above.
-gok

# dictionaries are big
-aspell-*
-hunspell-*
-man-pages-*
-words

# save some space
-gnome-user-docs
-gimp-help
-gimp-help-browser
-gnome-games
-gnome-games-help
totem-gstreamer
-totem-xine
-nss_db
-vino
-isdn4k-utils
-dasher
-evince-dvi
-evince-djvu
# not needed for gnome
-acpid

# these pull in excessive dependencies
-ekiga
-tomboy
-f-spot

##################### End default fedora ################

# Include these fonts but no foreign language fonts.
dejavu-sans-fonts
dejavu-sans-mono-fonts
dejavu-serif-fonts
ghostscript-fonts
liberation-mono-fonts
liberation-sans-fonts
liberation-serif-fonts
urw-fonts

# Selinux disabled, don't need these
-selinux-policy
-selinux-policy-targeted
-setroubleshoot
-policycoreutils-gui
-policycoreutils
-checkpolicy

# Don't need quota.
-quota

# NIS domains
-ypbind
-yp-tools
-nss_ldap
-nscd

# Use NFS for sharing instead of this webDAV stuff
# It pulls in all of apache.
-gnome-user-share
-httpd
-httpd-tools
-mod_dnssd
-apr
-apr-util
-apr-util-ldap

# Stuff for install to hard drive but I can't get it to work...
-anaconda
-busybox-anaconda
-smolt
-smolt-firstboot
# firstboot is needed for system-config-keyboard
#firstboot

# Irrelevant packages
-bug-buddy
-cheese
-nautilus-sendto
-openvpn
-system-config-language
-jwhois
-kerneloops
-krb5-workstation
-krb5-auth-dialog
-pam_krb5
-pcmciautils
-evolution
-evolution-perl
-evolution-help
-gnome-pilot
-gnome-media
-gimp*
-orca
-ImageMagick
-compiz-gnome
-lftp
-pidgin
-alacarte
-audit
-talk
-tcpdump
-telnet
-glx-utils
-sos
-logwatch
-iptstate
-fedora-bookmarks
-finger
-pam_passwdqc
-psacct
-nc
-totem*

# Mail command, have thunderbird
-mailx

# Only for hard drives
-smartmontools

# infrared
-irda-utils

# Useless for a single CPU.
-irqbalance

# Fingerpinrt stuff - maybe needed for security?
-gdm-plugin-fingerprint
-fprintd
-fprintd-pam
-libfprint
-libpst

# Car doesn't have a printer.
-cups
-cups-pk-helper
-printer-filters
-ptouch-driver
-foomatic
-system-config-printer
-system-config-printer-libs
-hplip-common
-hplip-libs
-libsane-hpaio

# CD rip/burning, maybe needed
-wodim
-brasero
-brasero-nautilus
-icedax
-cdparanoia
-sound-juicer

%end

%post
cat >> /etc/rc.d/init.d/livesys << EOF
# disable screensaver locking
gconftool-2 --direct --config-source=xml:readwrite:/etc/gconf/gconf.xml.defaults -s -t bool /apps/gnome-screensaver/lock_enabled false >/dev/null
# set up timed auto-login for after 60 seconds
cat >> /etc/gdm/custom.conf << FOE
[daemon]
TimedLoginEnable=true
TimedLogin=liveuser
TimedLoginDelay=1
FOE

EOF

%end

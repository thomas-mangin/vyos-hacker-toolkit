#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime

from vyosextra import log
from vyosextra import arguments
from vyosextra.config import config

from vyosextra.entry import build as control


class Control(control.Control):
    def docker(self, where):
        build_repo = config.get(where, 'repo')
        when = datetime.now().strftime('%Y%M%d%H%M')

        vyos_iso = f'{build_repo}/build/live-image-amd64.hybrid.iso'
        root_iso = f'{build_repo}/build/iso'
        root_oci = f'{build_repo}/build/oci'

        self.ssh(where, f'sudo rm -rf {root_iso} {root_oci}', exitonfail=False)
        self.ssh(where, f'sudo umount {root_iso}/', exitonfail=False)

        self.ssh(where, f'sudo mkdir -p {root_iso} {root_oci}')
        self.ssh(where, f'sudo mount -t iso9660  -o loop {vyos_iso} {root_iso}/')
        self.ssh(where, f'sudo unsquashfs -f -d {root_oci}/ {root_iso}/live/filesystem.squashfs')
        self.ssh(where, f"sudo sed -i 's/^LANG=.*$/LANG=C.UTF-8/' {root_oci}/etc/default/locale")
        self.ssh(where, f'sudo rm -rf {root_oci}/boot/*.img')
        self.ssh(where, f'sudo rm -rf {root_oci}/boot/*vyos*')
        self.ssh(where, f'sudo rm -rf {root_oci}/boot/vmlinuz')
        self.ssh(where, f'sudo rm -rf {root_oci}/vmlinuz')
        self.ssh(where, f'sudo rm -rf {root_oci}/usr/lib/x86_64-linux-gnu/libwireshark.so.*')
        self.ssh(where, f'sudo tar -C {root_oci} -c . | docker import - vyos:{when}')
        self.ssh(where, f'sudo umount {root_iso}/')
        self.ssh(where, f'sudo rm -rf {root_iso} {root_oci}')



def main():
    'convert an iso image to docker'

    arg = arguments.setup(__doc__, ['docker'])

    control = Control(arg.dry, not arg.quiet)

    control.docker(arg.server)

    log.completed('docker image built')


if __name__ == '__main__':
    main('iso')

import os


def get_host_distro():
    if not os.path.isfile('/etc/hostdistro'):
        return 'unknown'
    with open('/etc/hostdistro', 'tr') as hostdistro:
        return hostdistro.read().strip()

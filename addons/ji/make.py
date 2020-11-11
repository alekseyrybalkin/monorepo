import addons.ji.common as common


def prepare(pm):
    pkgbuild = common.source_pkgbuild(pm)


def make(pm):
    pkgbuild = common.source_pkgbuild(pm)
    print(pkgbuild)


def make_worker(pm):
    pass

import itertools
import os
import re
import subprocess
import tempfile

import addons.ji.common as common
import addons.ji.tarball as tarball
import addons.ji.queries as queries
import addons.shell as shell


def update_links(pm, query):
    shared_library_re = re.compile('^.*Shared library: \\[(.*)\\]$')

    package = common.find_package(pm, query)

    print('updating links for {}...'.format(package['name']))
    pm.db.execute('delete from depends where user_id=?', (package['id'],))

    libs = set()
    for item in queries.db_list_files(pm, package['name']):
        if not any(item.endswith(ext) for ext in pm.config['readelf_skip_extensions']):
            try:
                readelf = shell.output('readelf --dynamic {}'.format(item))
            except subprocess.CalledProcessError:
                continue
            for line in readelf.split('\n'):
                if 'Shared library' in line:
                    link = os.path.join('/usr/lib', shared_library_re.match(line).groups(1)[0])
                    if os.path.islink(link):
                        lib = os.readlink(link)
                        if not lib.startswith('/'):
                            lib = os.path.join(os.path.dirname(link), lib)
                    else:
                        lib = link
                    libs.add(lib)

    owner_ids = set()
    for lib in libs:
        for owner in queries.who_owns(pm, lib):
            owner_ids.add(owner['id'])

    for owner_id in owner_ids:
        pm.db.execute('insert into depends(user_id, provider_id) values (?, ?)', (package['id'], owner_id))


def update_new_tarballs(pm):
    updated = set()

    packages_path = os.path.join(pm.config['data_path'], 'installed')

    actual_package_set = set()
    for package_file in os.listdir(packages_path):
        filename = os.path.join(packages_path, package_file)
        timestamp = int(os.stat(filename).st_mtime)

        query = package_file.replace(tarball.get_tarball_suffix(), '')
        package, version = query.rsplit('-', 1)

        actual_package_set.add(query)

        stored_package = common.find_package(pm, query, none_ok=True)
        if stored_package is None or int(stored_package['timestamp']) != timestamp:
            depending_list = []
            if stored_package is not None:
                pm.db.execute('delete from file where package_id=?', (stored_package['id'],))
                pm.db.execute('delete from package where id=?', (stored_package['id'],))
                pm.db.execute('delete from depends where user_id=?', (stored_package['id'],))
                sql = '''
                    select package.id as id from depends
                         join package on depends.user_id = package.id where
                         depends.provider_id = ? and provider_id <> user_id
                '''
                for depending in pm.db.select_many(sql, (stored_package['id'],)):
                    depending_list.append(depending['id'])
                pm.db.execute('delete from depends where provider_id = ?', (stored_package['id'],))

            updated.add(package)

            pm.db.execute(
                'insert into package(name, version, timestamp) values (?, ?, ?)',
                (package, version, timestamp),
            )
            stored_package = common.find_package(pm, query)
            package_id = stored_package['id']

            files = []

            # regular files and directories
            for item in itertools.chain(tarball.list_dirs(pm, filename), tarball.list_files(pm, filename)):
                files.append((
                    package_id,
                    1 if item.isdir() else 0,
                    '{}/{}'.format(item.uname, item.gname),
                    os.path.join('/', item.name),
                    item.linkname,
                    0,
                ))

            # generated files
            with tempfile.TemporaryDirectory() as tmpdir:
                relative_path = os.path.join('usr/share', pm.config['exe'], '{}.PKGBUILD'.format(package))
                tarball.extract_file(filename, relative_path, tmpdir)
                pkgbuild = common.source_pkgbuild(pm, pkgbuild=os.path.join(tmpdir, relative_path))
                for generated_file in pkgbuild['generated_files'].strip().split(' '):
                    if generated_file:
                        files.append((
                            package_id,
                            0,
                            'root/root',
                            os.path.join('/', generated_file),
                            '',
                            1,
                        ))

            pm.db.executemany(
                '''
                    insert into file(package_id, is_dir, ownership, name, link, is_generated)
                        values (?, ?, ?, ?, ?, ?)
                ''',
                files,
            )
            for depending in depending_list:
                pm.db.execute(
                    'insert into depends(user_id, provider_id) values (?, ?)',
                    (depending, package_id),
                )

    # now delete stale packages from db
    package_ids_to_delete = []
    for row in pm.db.select_many('select id, name, version from package'):
        if '{}-{}'.format(row['name'], row['version']) not in actual_package_set:
            package_ids_to_delete.append(row['id'])
    for package_id in package_ids_to_delete:
        pm.db.execute('delete from file where package_id = ?', (package_id,))
        pm.db.execute('delete from package where id = ?', (package_id,))
        pm.db.execute('delete from depends where user_id = ?', (package_id,))
        pm.db.execute('delete from depends where provider_id = ?', (package_id,))

    return updated


def gen_db(pm):
    for fresh_package in update_new_tarballs(pm):
        update_links(pm, fresh_package)

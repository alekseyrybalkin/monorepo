def ls(pm):
    for row in pm.db.select_many('select name, version from package order by name'):
        print('{}-{}'.format(row['name'], row['version']))

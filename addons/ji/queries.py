def ls(pm):
    for row in pm.db.select_many('select name, version from package order by name'):
        print('{}-{}'.format(row['name'], row['version']))


def db_list_files(pm, query):
    sql = "select id, name, version from package where name = ? or name || '-' || version = ?;"
    package = pm.db.select_one(sql, (query, query))
    if not package:
        raise RuntimeError('package {} is not installed'.format(query))

    sql = """
        select name from file where package_id = ?
            and permissions not like 'd%'
            and (is_generated is null or is_generated = 0)
        order by name
    """
    for row in pm.db.select_many(sql, (package['id'],)):
        print(row['name'])

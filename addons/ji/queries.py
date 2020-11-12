import addons.ji.common as common


def ls(pm):
    result = []
    for row in pm.db.select_many('select name, version from package order by name'):
        result.append('{}-{}'.format(row['name'], row['version']))
    return result


def db_list_files(pm, query):
    package = common.find_package(pm, query)

    result = []
    sql = """
        select name from file where package_id = ?
            and is_dir = 0
            and (is_generated is null or is_generated = 0)
        order by name
    """
    for row in pm.db.select_many(sql, (package['id'],)):
        result.append(row['name'])
    return result


def db_list_generated(pm, query):
    package = common.find_package(pm, query)

    result = []
    sql = """
        select name from file where package_id = ?
            and is_dir = 0
            and is_generated = 1
        order by name
    """
    for row in pm.db.select_many(sql, (package['id'],)):
        result.append(row['name'])
    return result


def db_list_dirs(pm, query):
    package = common.find_package(pm, query)

    result = []
    sql = """
        select name from file where package_id = ?
            and is_dir = 1
        order by name
    """
    for row in pm.db.select_many(sql, (package['id'],)):
        result.append(row['name'])
    return result


def who_uses_dir(pm, query):
    query = query.rstrip('/')

    result = []
    sql = """
        select name, version from package where id in
            (select distinct package_id from file where name = ? and is_dir = 1)
        order by name
    """
    for row in pm.db.select_many(sql, (query + '/',)):
        result.append('{}-{}'.format(row['name'], row['version']))
    return result


def who_owns(pm, query):
    result = []
    sql = """
        select id, name, version from package where id in
            (select distinct package_id from file where name = ? and is_dir = 0)
        order by name
    """
    return pm.db.select_many(sql, (query,))


def list_duplicates(pm):
    result = []
    sql = """
        select cnt, name from
            (
                select count(id) as cnt, name from file
                    where is_dir = 0
                    group by name
                    order by cnt desc
            )
            where cnt > 1
    """
    for row in pm.db.select_many(sql):
        result.append('{}  {}'.format(row['name'], row['cnt']))
    return result

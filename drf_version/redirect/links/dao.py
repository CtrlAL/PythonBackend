import os

_session = None

def get_session():
    global _session
    if _session is None:
        import cassandra.cluster
        from cassandra.query import dict_factory
        hosts = os.environ.get("SCYLLA_HOSTS", "127.0.0.1").split(",")
        cluster = cassandra.cluster.Cluster(hosts)
        _session = cluster.connect()
        _session.row_factory = dict_factory
        _session.execute("CREATE KEYSPACE IF NOT EXISTS urlshort WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
        _session.set_keyspace("urlshort")
        _session.execute("CREATE TABLE IF NOT EXISTS links (code text PRIMARY KEY, long_url text)")
    return _session

def get_long_url(code):
    row = get_session().execute("SELECT long_url FROM links WHERE code=%s", (code,)).one()
    return row["long_url"] if row else None

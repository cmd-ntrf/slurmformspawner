from datetime import datetime
from json import loads
from subprocess import check_output, CalledProcessError

from cachetools import TTLCache, cached

INFO_CACHE_TTL = 60
ACCT_CACHE_SIZE = 100
ACCT_CACHE_TTL = 60
RES_CACHE_TTL = 60

class CustomTTLCache(TTLCache):
    def set_ttl(self, ttl):
        if ttl != self._TTLCache__ttl:
            self._TTLCache__ttl = ttl
            self.clear()

_info_cache = CustomTTLCache(maxsize=1, ttl=INFO_CACHE_TTL)
_acct_cache = CustomTTLCache(maxsize=ACCT_CACHE_SIZE, ttl=ACCT_CACHE_TTL)
_res_cache = CustomTTLCache(maxsize=1, ttl=RES_CACHE_TTL)

def set_info_cache_ttl(ttl):
    _info_cache.set_ttl(ttl)

def set_acct_cache_ttl(ttl):
    _acct_cache.set_ttl(ttl)

def set_res_cache_ttl(ttl):
    _res_cache.set_ttl(ttl)

@cached(_info_cache)
def get_node_info():
    output = {'cpu': [], 'mem': [], 'gres': []}
    try:
        infos = check_output(['sinfo', '-h', '-e',
                              '--format={"cpu":%c,"mem":%m,"gres":"%G"}'], encoding='utf-8')
    except CalledProcessError:
        return output
    else:
        infos = [loads(i) for i in infos.split()]
        infos = {key: [dict_[key] for dict_ in infos] for key in infos[0]}
    return infos

def get_cpus():
    cpus = set(get_node_info()['cpu'])
    return sorted(cpus)

def get_mems():
    mems = set(get_node_info()['mem'])
    return sorted(mems)

def get_gres():
    gres = set(get_node_info()['gres'])
    if '(null)' in gres:
        gres.remove('(null)')
    return ['gpu:0'] + sorted(gres)

@cached(_acct_cache)
def get_accounts(username):
    try:
        accounts = check_output(['sacctmgr', 'show', 'user', username, 'withassoc',
                                 'format=account', '-p', '--noheader'], encoding='utf-8')
    except CalledProcessError:
        accounts = []
    else:
        accounts = accounts.split()
    return [account.rstrip('|') for account in accounts]

@cached(_res_cache)
def get_reservations():
    try:
        reservations = check_output(['scontrol', 'show', 'res', '-o', '--quiet'], encoding='utf-8')
    except CalledProcessError:
        reservations = []
    else:
        if reservations:
            reservations = reservations.strip().split('\n')
        else:
            reservations = []

    reservations = [dict([item.split('=', maxsplit=1) for item in res.split()]) for res in reservations if res]
    for res in reservations:
        res['Users'] = set(res['Users'].split(','))
        res['Accounts'] = set(res['Accounts'].split(','))
        res['StartTime'] = datetime.strptime(res['StartTime'], "%Y-%m-%dT%H:%M:%S")
        res['EndTime'] = datetime.strptime(res['EndTime'], "%Y-%m-%dT%H:%M:%S")
    return reservations

def get_active_reservations(username, accounts):
    reservations = get_reservations()
    if not reservations:
        return []

    accounts = set(accounts)
    active_res = []
    now = datetime.now()
    return [
        res for res in reservations
        if (
            res['StartTime'] <= now <= res['EndTime'] and
            (
                username in res['Users'] or
                bool(accounts.intersection(res['Accounts']))
            )
        )
    ]

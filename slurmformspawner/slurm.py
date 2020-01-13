from datetime import datetime
from subprocess import check_output

def get_cpus():
    cpus = check_output(['sinfo', '-h', '-e', '--format=%c'], encoding='utf-8').split()
    return list(map(int, cpus))

def get_mems():
    mems = check_output(['sinfo', '-h', '-e', '--format=%m'], encoding='utf-8').split()
    return list(map(int, mems))

def get_accounts(username):
    output = check_output(['sacctmgr', 'show', 'user', username, 'withassoc',
                           'format=account', '-p', '--noheader'], encoding='utf-8').split()
    return [out.rstrip('|') for out in output]

def get_gres():
    return ['gpu:0'] + check_output(['sinfo', '-h', '--format=%G'], encoding='utf-8').split()

def get_active_reservations(username, accounts):
    accounts = set(accounts)
    reservations = check_output(['scontrol', 'show', 'res', '-o', '--quiet'], encoding='utf-8').strip().split('\n')
    if not reservations:
        return []
    reservations = [dict([item.split('=', maxsplit=1) for item in rsv.split()]) for rsv in reservations if rsv]
    for rsv in reservations:
        if rsv['State'] == 'ACTIVE':
            rsv['Users'] = set(rsv['Users'].split(','))
            rsv['Accounts'] = set(rsv['Accounts'].split(','))
            rsv['StartTime'] = datetime.strptime(rsv['StartTime'], "%Y-%m-%dT%H:%M:%S")
            rsv['EndTime'] = datetime.strptime(rsv['EndTime'], "%Y-%m-%dT%H:%M:%S")
            rsv['valid'] = username in rsv['Users'] or bool(accounts.intersection(rsv['Accounts']))
        else:
            rsv['valid'] = False
    return [rsv for rsv in reservations if rsv['valid']]

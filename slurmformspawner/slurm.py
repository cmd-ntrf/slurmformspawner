from json import loads
from operator import attrgetter
from traitlets.config import SingletonConfigurable
from traitlets import Integer

from datetime import datetime
from subprocess import check_output, CalledProcessError

from cachetools import TTLCache, cachedmethod


class SlurmAPI(SingletonConfigurable):
    info_cache_ttl = Integer(300).tag(config=True)
    acct_cache_ttl = Integer(300).tag(config=True)
    acct_cache_size = Integer(100).tag(config=True)
    res_cache_ttl = Integer(300).tag(config=True)

    def __init__(self, config=None):
        super().__init__(config=config)
        self.info_cache = TTLCache(maxsize=1, ttl=self.info_cache_ttl)
        self.acct_cache = TTLCache(
            maxsize=self.acct_cache_size, ttl=self.acct_cache_ttl
        )
        self.res_cache = TTLCache(maxsize=1, ttl=self.res_cache_ttl)

    @cachedmethod(attrgetter("info_cache"))
    def get_node_info(self):
        output = {
            "cpu": set(),
            "mem": set(),
            "gres": set(),
            "partitions": set(),
            "features": set(),
        }
        try:
            show_node_str = check_output(
                ["scontrol", "-o", "show", "node", "--json"], encoding="utf-8"
            )
        except CalledProcessError:
            return output

        show_node_map = loads(show_node_str)
        for node in show_node_map["nodes"]:
            output["cpu"].add(node["cpus"])
            output["mem"].add(node["real_memory"] - node.get("specialized_memory", 0))
            output["gres"].update(node["gres"].split(","))
            output["partitions"].update(node["partitions"])
            output["features"].update(node["features"])
        return output

    def is_online(self):
        return self.get_node_info()["cpu"] and self.get_node_info()["mem"]

    def get_cpus(self):
        return sorted(self.get_node_info()["cpu"])

    def get_mems(self):
        return sorted(self.get_node_info()["mem"])

    def get_gres(self):
        gres = self.get_node_info()["gres"].copy()
        if "(null)" in gres:
            gres.remove("(null)")
        return ["gpu:0"] + sorted(gres)

    def get_partitions(self):
        return sorted(self.get_node_info()["partitions"])

    @cachedmethod(attrgetter("acct_cache"))
    def get_accounts(self, username):
        try:
            string = check_output(
                [
                    "sacctmgr",
                    "show",
                    "user",
                    username,
                    "withassoc",
                    "format=account",
                    "-P",
                    "--noheader",
                ],
                encoding="utf-8",
            )
        except CalledProcessError:
            return []
        return string.split()

    @cachedmethod(attrgetter("res_cache"))
    def get_reservations(self):
        try:
            reservations = check_output(
                ["scontrol", "show", "res", "-o", "--quiet"], encoding="utf-8"
            )
        except CalledProcessError:
            reservations = []
        else:
            if reservations:
                reservations = reservations.strip().split("\n")
            else:
                reservations = []

        reservations = [
            dict([item.split("=", maxsplit=1) for item in res.split()])
            for res in reservations
            if res
        ]
        for res in reservations:
            res["Users"] = set(res["Users"].split(","))
            res["Accounts"] = set(res["Accounts"].split(","))
            res["StartTime"] = datetime.strptime(res["StartTime"], "%Y-%m-%dT%H:%M:%S")
            res["EndTime"] = datetime.strptime(res["EndTime"], "%Y-%m-%dT%H:%M:%S")
        return reservations

    def get_active_reservations(self, username, accounts):
        reservations = self.get_reservations()
        if not reservations:
            return []

        accounts = set(accounts)
        now = datetime.now()
        return [
            res
            for res in reservations
            if (
                res["StartTime"] <= now <= res["EndTime"]
                and (
                    username in res["Users"]
                    or bool(accounts.intersection(res["Accounts"]))
                )
            )
        ]

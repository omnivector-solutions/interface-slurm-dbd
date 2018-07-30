import charms.reactive as reactive
import socket

from charmhelpers.contrib.templating.contexts import dict_keys_without_hyphens
from charmhelpers.core.hookenv import (
    DEBUG,
    log,
)


class DbdProvides(reactive.Endpoint):
    # TODO
    pass

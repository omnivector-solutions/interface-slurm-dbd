import charms.reactive.flags as flags
import charms.reactive as reactive
import charmhelpers.core.hookenv as hookenv
#
import socket

from charmhelpers.core.hookenv import (
    log,
    status_set,
)


class DbdRequires(reactive.Endpoint):

    def configure_dbd(self, clustername):
        ctxt = {'requested_clustername': clustername}
     
        for relation in self.relations:
            relation.to_publish.update(ctxt)

    @reactive.when('slurm-controller.dbdname-requested')
    @reactive.when_not('slurm-controller.dbdname-accepted')
    @reactive.when('endpoint.slurm-dbd-consumer.changed.accepted_clustername')
    def get_clustername_ack(self):
        epunit = hookenv.remote_unit()
        hookenv.log("get_clustername_ack(): remote unit: %s" % epunit)
        joined_units = self.all_joined_units

        # also pick up ip-adress etc to dbd here
        if epunit != None:
            namerequest = joined_units[epunit].received.get('requested_clustername')
            nameresult = joined_units[epunit].received.get('accepted_clustername')
            dbd_host = joined_units[epunit].received.get('dbd_host')
            if nameresult:
                hookenv.log("get_clustername_ack(): name %s was accepted by %s on %s" % (nameresult, epunit, dbd_host))
                # all is fine
                flags.set_flag('slurm-controller.dbdname-accepted')
            else:
                status_set('blocked', 'Cluster name %s rejected by DBD on %s: name already taken. Run juju config <slurm-controller-charm> clustername=New_Name' % (namerequest, epunit))
                hookenv.log("get_clustername_ack(): request for %s was rejected by %s" % (namerequest, epunit))
                flags.clear_flag('slurm-controller.dbdname-requested')

            """
            TODO: raise some flag so that layer-slurm-controller reconfigures
            itself+peers and updates config on all nodes
            """
        # clear all the flags that was sent in changed() on the provider side
        flags.clear_flag('endpoint.slurm-dbd-consumer.changed.requested_clustername')
        flags.clear_flag('endpoint.slurm-dbd-consumer.changed.accepted_clustername')

    @reactive.when('endpoint.slurm-dbd-consumer.changed.dbd_host')
    def store_dbd_host(self):
        epunit = hookenv.remote_unit()
        hookenv.log("store_dbd_host(): remote unit: %s" % epunit)
        joined_units = self.all_joined_units

        # also pick up ip-adress etc to dbd here
        if epunit != None:
            nameresult = joined_units[epunit].received.get('dbd_host')
            self._cached_dbd_host = nameresult
            portresult = joined_units[epunit].received.get('dbd_port')
            self._cached_dbd_port = portresult
            ipresult = joined_units[epunit].received.get('ingress-address')
            self._cached_dbd_ipaddr = ipresult
            hookenv.log("store_dbd_host(): received hostname/ip %s/%s:%s from %s" % (nameresult, ipresult, portresult, epunit))
            flags.set_flag('endpoint.slurm-dbd-consumer.dbd_host_updated')

        flags.clear_flag('endpoint.slurm-dbd-consumer.changed.dbd_host')

    @property
    def dbd_host(self):
        return self._cached_dbd_host

    @property
    def dbd_port(self):
        return self._cached_dbd_port

    @property
    def dbd_ipaddr(self):
        return self._cached_dbd_ipaddr

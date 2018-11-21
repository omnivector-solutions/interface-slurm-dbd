import charms.reactive as reactive
import socket
import subprocess
import charmhelpers.core.hookenv as hookenv

import charms.reactive.flags as flags

from charmhelpers.contrib.templating.contexts import dict_keys_without_hyphens
from charmhelpers.core.hookenv import (
    DEBUG,
    log,
)


class DbdProvides(reactive.Endpoint):

    # TODO: consider moving stuff from the interface to layer DBD instead?
    def test_if_busy(self, clustername):
        hookenv.log("test_is_busy(): testing if %s is busy" % clustername)
        cmd = "/usr/bin/sacctmgr list cluster %s -n" % clustername
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        (output, err) = p.communicate()
        # Wait for sacctmgr to terminate and get the return code
        p_status = p.wait()
        hookenv.log("test_is_busy(): list cluster stdout: %s" % output)
        hookenv.log("test_is_busy(): list cluster stderr: %s" % err)
        hookenv.log("Command exit status/return code: %s" % p_status)
        if clustername in output:
            return True

        # create the cluster:
        cmd = "/usr/bin/sacctmgr add cluster %s -i" % clustername
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
        (output, err) = p.communicate()
        # Wait for sacctmgr to terminate and get the return code
        p_status = p.wait()
        hookenv.log("test_is_busy(): create cluster stdout: %s" % output)
        hookenv.log("test_is_busy(): create cluster stderr: %s" % err)
        hookenv.log("Command exit status/return code: %s" % p_status)
 
        return False

    @reactive.when('endpoint.slurm-dbd-provider.joined')
    @reactive.when('endpoint.slurm-dbd-provider.changed')
    @reactive.when('endpoint.slurm-dbd-provider.changed.requested_clustername')
    def changed(self, event=None, even2=None):
        epunit = hookenv.remote_unit()

        if epunit != None:
            hookenv.log("changed(): %s" % epunit)
            joined_units = self.all_joined_units
            namerequest = joined_units[epunit].received.get('requested_clustername')
            if namerequest:
                hookenv.log("changed(): received name request %s from %s" % (namerequest, epunit))
                busy = self.test_if_busy(namerequest)
                if busy:
                    hookenv.log("changed(): request %s from %s denied, busy" % (namerequest, epunit))
                    accepted = None
                else:
                    hookenv.log("changed(): request %s from %s accepted" % (namerequest, epunit))
                    accepted = namerequest

                dbd_host = socket.gethostname()
                cfg = hookenv.config()
                dbd_port = cfg['slurmdbd_port']
                ctxt = {'requested_clustername': namerequest,
                        'accepted_clustername': accepted,
                        'dbd_host': dbd_host,
                        'dbd_port': dbd_port}

                # publicera ctxt on the relation for this particular unit
                for relation in self.relations:
                    # Get a list of RelatedUnits
                    for unit in relation.joined_units:
                        if unit.unit_name == epunit:
                            hookenv.log("changed(): acking/nacking %s to %s" % (namerequest, unit.unit_name))
                            relation.to_publish.update(ctxt)
                        else:
                            hookenv.log("changed(): not publishing update to %s, wrong relation!" % unit.unit_name)

        flags.clear_flag('endpoint.slurm-dbd-provider.changed.requested_clustername')

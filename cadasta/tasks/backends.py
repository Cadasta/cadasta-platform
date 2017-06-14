from celery.backends.rpc import RPCBackend


class ResultQueueRPC(RPCBackend):
    # TODO: Ensure result queues auto_delete. Results are put into a
    # queue for each consumer. When that consumer disconnects, that
    # queue should delete.

    def _create_exchange(self, name, type='direct', delivery_mode=2):
        # Use app's provided exchange information rather than an unnamed
        # direct exchange
        return self.Exchange(name=name, type=type, delivery_mode=delivery_mode)

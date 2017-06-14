from celery import Task as _Task
from celery.backends.rpc import RPCBackend


class Task(_Task):
    def log(self, msg):
        """ Helper to compose log messages """
        return self.update_state(meta={'log': msg})


class ResultQueueRPC(RPCBackend):

    def _create_exchange(self, name, type='direct', delivery_mode=2):
        # Use app's provided exchange information rather than a RPCBackend's
        # default of an unnamed direct exchange
        return self.Exchange(name=name, type=type, delivery_mode=delivery_mode)

    def store_result(self, *args, **kwargs):
        # Ensure that 'reply_to' queue is registered with exchange, so
        # that results are routed to both 'reply_to' queue and result
        # queue.
        # TODO: This may be cleaner if we override
        # kombu.transport.virtual.base.Channel.exchange_types with a new
        # type of 'topic' class that always returns the routing_key when
        # routing
        reply_to = kwargs.get('request', {}).get('reply_to')
        if not reply_to:
            return super(ResultQueueRPC, self).store_result(*args, **kwargs)

        with self.app.pool.acquire_channel(block=True) as (_, channel):
            channel.queue_bind(
                reply_to, self.exchange.name, routing_key=reply_to)
            try:
                return super(ResultQueueRPC, self).store_result(*args, **kwargs)
            finally:
                channel.queue_unbind(
                    reply_to, self.exchange.name, routing_key=reply_to)

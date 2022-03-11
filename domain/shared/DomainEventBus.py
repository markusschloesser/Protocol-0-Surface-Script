import inspect
from functools import partial

from typing import Dict, List, Type, Callable, TYPE_CHECKING

from protocol0.domain.shared.scheduler.Scheduler import Scheduler

if TYPE_CHECKING:
    from protocol0.shared.sequence.Sequence import Sequence  # noqa


class DomainEventBus(object):
    _registry = {}  # type: Dict[Type, List[Callable]]

    @classmethod
    def one(cls, domain_event, subscriber):
        # type: (Type, Callable) -> None
        """ helper method for unique reaction """
        def execute(_):
            subscriber()
            cls.un_subscribe(domain_event, execute)

        cls.subscribe(domain_event, execute)

    @classmethod
    def subscribe(cls, domain_event, subscriber):
        # type: (Type, Callable) -> None
        args = inspect.getargspec(subscriber).args
        if "self" in args:
            args = args[1:]
        assert len(args) == 1, "The subscriber should have a unique parameter for the event : %s" % subscriber

        if domain_event not in cls._registry:
            cls._registry[domain_event] = []

        if subscriber not in cls._registry[domain_event]:
            cls._registry[domain_event].append(subscriber)

    @classmethod
    def un_subscribe(cls, domain_event, subscriber):
        # type: (Type, Callable) -> None
        if domain_event in cls._registry and subscriber in cls._registry[domain_event]:
            cls._registry[domain_event].remove(subscriber)

    @classmethod
    def notify(cls, domain_event):
        # type: (object) -> None
        if type(domain_event) in cls._registry:
            # protect the list from unsubscribe in subscribers
            subscribers = cls._registry[type(domain_event)][:]
            for subscriber in subscribers:
                subscriber(domain_event)

    @classmethod
    def defer_notify(cls, domain_event):
        # type: (object) -> None
        """ for events notified in listeners we can defer to avoid the changes by notification error"""
        Scheduler.defer(partial(cls.notify, domain_event))

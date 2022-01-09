from collections import defaultdict
from functools import partial, wraps

from typing import TYPE_CHECKING, Any, Callable

from _Framework.SubjectSlot import subject_slot as _framework_subject_slot
from protocol0.errors.Protocol0Warning import Protocol0Warning
from protocol0.my_types import Func, T
from protocol0.utils.utils import is_method

if TYPE_CHECKING:
    from protocol0.components.Push2Manager import Push2Manager
    from protocol0.utils.callback_descriptor import CallbackDescriptor


def push2_method(defer_call=True):
    # type: (bool) -> Callable
    def wrap(func):
        # type: (Func) -> Func
        @wraps(func)
        def decorate(self, *a, **k):
            # type: (Push2Manager, Any, Any) -> Any
            # check hasattr in case the push2 is turned off during a set
            if not self.push2 or not hasattr(self.push2, "_initialized") or not self.push2._initialized:
                return

            def execute():
                # type: () -> Any
                with self.push2.component_guard():
                    return func(self, *a, **k)

            if defer_call:
                self.parent.defer(execute)
            else:
                return execute()

        return decorate

    return wrap


EXPOSED_P0_METHODS = {}


def api_exposable_class(cls):
    # type: (T) -> T
    for name, method in cls.__dict__.iteritems():
        if hasattr(method, "api_exposed"):
            EXPOSED_P0_METHODS[name] = cls
    return cls


def api_exposed(func):
    # type: (Func) -> Func
    func.api_exposed = True  # type: ignore
    return func


def p0_subject_slot(event, immediate=False):
    # type: (str, bool) -> Callable[[Callable], CallbackDescriptor]
    """
    Drop in replacement of _Framework subject_slot decorator
    Extends its behavior to allow the registration of callbacks that will execute after the decorated function finished
    By default the callbacks execution is deferred to prevent the dreaded "Changes cannot be triggered by notifications. You will need to defer your response"
    immediate=True executes the callbacks immediately (synchronously)

    This decorator / callback registration is mainly used by the Sequence pattern
    It allows chaining functions by reacting to listeners being triggered and is paramount to executing asynchronous sequence of actions
    Sequence.add(complete_on=<@p0_subject_slot<listener>> will actually registers a callback on the decorated <listener>.
    This callback will resume the sequence when executed.
    """

    def wrap(func):
        # type: (Callable) -> CallbackDescriptor
        def decorate(*a, **k):
            # type: (Any, Any) -> None
            func(*a, **k)

        decorate.original_func = func  # type: ignore[attr-defined]

        callback_descriptor = has_callback_queue(immediate)(_framework_subject_slot(event)(decorate))

        return callback_descriptor

    return wrap


def has_callback_queue(immediate=False):
    # type: (bool) -> Callable[[Callable], CallbackDescriptor]
    def wrap(func):
        # type: (Callable) -> CallbackDescriptor
        from protocol0.utils.callback_descriptor import CallbackDescriptor

        return CallbackDescriptor(func, immediate)

    return wrap


def log(func):
    # type: (Func) -> Func
    @wraps(func)
    def decorate(*a, **k):
        # type: (Any, Any) -> Any
        func_name = func.__name__
        args = [str(arg) for arg in a] + ["%s=%s" % (key, str(value)) for (key, value) in k.items()]
        if is_method(func):
            func_name = "%s.%s" % (a[0].__class__.__name__, func_name)
            args = args[1:]
        message = func_name + "(%s)" % (", ".join([str(arg) for arg in args]))

        from protocol0 import Protocol0

        Protocol0.SELF.log_info("-- %s" % message, debug=False)
        return func(*a, **k)

    return decorate


def handle_error(func):
    # type: (Func) -> Func
    @wraps(func)
    def decorate(*a, **k):
        # type: (Any, Any) -> Any
        from protocol0 import Protocol0

        # noinspection PyBroadException
        try:
            return func(*a, **k)
        except Protocol0Warning as e:
            Protocol0.SELF.show_message(e.message)
        except Exception:
            from protocol0 import Protocol0

            Protocol0.SELF.errorManager.handle_error()

    return decorate


def debounce(wait_time=100):
    # type: (int) -> Callable
    """ here we make the method dynamic """

    def wrap(func):
        # type: (Callable) -> Callable
        @wraps(func)
        def decorate(*a, **k):
            # type: (Any, Any) -> None
            object_source = a[0] if is_method(func) else decorate
            decorate.count[object_source] += 1  # type: ignore[attr-defined]
            from protocol0 import Protocol0

            Protocol0.SELF.wait(wait_time, partial(execute, func, *a, **k))

        decorate.count = defaultdict(int)  # type: ignore[attr-defined]

        def execute(real_func, *a, **k):
            # type: (Callable, Any, Any) -> Any
            object_source = a[0] if is_method(real_func) else decorate
            decorate.count[object_source] -= 1  # type: ignore[attr-defined]
            if decorate.count[object_source] == 0:  # type: ignore[attr-defined]
                return real_func(*a, **k)

        return decorate

    return wrap


def throttle(wait_time=100):
    # type: (int) -> Callable
    def wrap(func):
        # type: (Callable) -> Callable
        @wraps(func)
        def decorate(*a, **k):
            # type: (Any, Any) -> Any
            object_source = a[0] if is_method(func) else decorate

            if decorate.paused[object_source] and k.get("throttle", True):
                return

            decorate.paused[object_source] = True
            res = func(*a, **k)

            def activate():
                # type: () -> None
                decorate.paused[object_source] = False

            from protocol0 import Protocol0
            Protocol0.SELF.wait(wait_time, activate)
            return res

        decorate.paused = defaultdict(lambda: False)  # type: ignore[attr-defined]

        return decorate

    return wrap


def prompt(question):
    # type: (str) -> Callable
    def wrap(func):
        # type: (Callable) -> Callable
        @wraps(func)
        def decorate(*a, **k):
            # type: (Any, Any) -> None
            from protocol0.sequence.Sequence import Sequence

            seq = Sequence()
            seq.prompt(question)
            seq.add(partial(func, *a, **k))
            seq.done()

        return decorate

    return wrap


def single_undo(func):
    # type: (Callable) -> Callable
    @wraps(func)
    def decorate(*a, **k):
        # type: (Any, Any) -> None
        from protocol0 import Protocol0

        Protocol0.SELF.protocol0_song.begin_undo_step()
        res = func(*a, **k)
        Protocol0.SELF.protocol0_song.end_undo_step()
        return res

    return decorate

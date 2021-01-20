from __future__ import print_function
import pytest
from a_protocol_0.sequence.Sequence import Sequence
from a_protocol_0.errors.SequenceError import SequenceError
from a_protocol_0.sequence.SequenceState import SequenceState, SequenceLogLevel
from a_protocol_0.tests.test_all import p0
from a_protocol_0.utils.decorators import has_callback_queue
from a_protocol_0.utils.utils import nop


def test_sanity_checks():
    with p0.component_guard():
        seq = Sequence(log_level=SequenceLogLevel.disabled)
        seq.done()
        assert seq._state == SequenceState.TERMINATED

        with pytest.raises(SequenceError):
            seq.add(wait=3)

        with pytest.raises(SequenceError):
            Sequence(log_level=SequenceLogLevel.disabled).done().done()


def test_simple_timeout():
    with p0.component_guard():
        seq = Sequence(log_level=SequenceLogLevel.disabled)
        seq.add(nop, complete_on=lambda: False, name="timeout step", check_timeout=0)
        seq.add(nop, name="unreachable step")
        seq.done()

        assert seq._state == SequenceState.TERMINATED
        assert seq._errored


def test_callback_timeout():
    class Example:
        @has_callback_queue
        def listener(self):
            pass

    obj = Example()

    seq = Sequence(log_level=SequenceLogLevel.disabled)
    seq.add(nop, complete_on=obj.listener, name="timeout step", check_timeout=0)
    seq.add(nop, name="unreachable step")
    seq.done()

    assert seq._state == SequenceState.TERMINATED
    assert seq._errored

    seq = Sequence(log_level=SequenceLogLevel.disabled)
    seq.add(nop, complete_on=obj.listener, name="timeout step", check_timeout=1)
    seq.add(nop, name="unreachable step")
    seq.done()
    obj.listener()

    assert seq._state == SequenceState.TERMINATED
    assert not seq._errored


def test_async_callback_timeout():
    class Example:
        @has_callback_queue
        def listener(self):
            seq = Sequence(log_level=SequenceLogLevel.disabled)
            seq.add(wait=1)
            seq.done()

    obj = Example()

    with p0.component_guard():
        seq = Sequence(log_level=SequenceLogLevel.disabled)
        seq.add(nop, complete_on=obj.listener, name="timeout step", check_timeout=2)
        seq.add(nop, name="after listener step")
        seq.done()
        obj.listener()

        assert seq._state == SequenceState.TERMINATED
        assert not seq._errored

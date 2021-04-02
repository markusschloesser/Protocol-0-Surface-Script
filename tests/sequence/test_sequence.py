import pytest
from transitions import MachineError

from a_protocol_0.sequence.Sequence import Sequence
from a_protocol_0.sequence.SequenceState import SequenceState, SequenceLogLevel
# noinspection PyUnresolvedReferences
from a_protocol_0.tests.test_all import p0
from a_protocol_0.utils.decorators import has_callback_queue
from a_protocol_0.utils.utils import nop


def test_sanity_checks():
    seq = Sequence(silent=True)
    seq.done()
    assert seq.terminated

    with pytest.raises(Exception):
        seq.add(wait=1)

    with pytest.raises(Exception):
        Sequence(silent=True).done().done()


def test_state_machine():
    seq = Sequence(silent=True)
    seq.dispatch("start")

    with pytest.raises(MachineError):
        seq.dispatch("start")

    with pytest.raises(MachineError):
        seq = Sequence(silent=True)
        seq._state_machine.state = SequenceState.TERMINATED
        seq.dispatch("start")


def test_no_timeout():
    seq = Sequence(silent=True)
    seq.add(nop, complete_on=lambda: False, name="timeout step", check_timeout=0)
    seq.add(nop, name="unreachable step")
    seq.done()

    assert seq.terminated


def test_callback_timeout():
    class Example:
        @has_callback_queue
        def listener(self):
            pass

    obj = Example()

    seq = Sequence(silent=True)
    seq.add(nop, complete_on=obj.listener, name="timeout step", check_timeout=1)
    seq.add(nop, name="unreachable step")
    seq.done()
    obj.listener()

    assert seq.terminated


def test_async_callback_execution_order():
    test_res = []

    class Example:
        @has_callback_queue
        def listener(self):
            seq = Sequence(silent=True)
            seq.add(lambda: test_res.append(0))
            seq.add(wait=1)
            seq.add(lambda: test_res.append(1))
            return seq.done()

    obj = Example()

    seq = Sequence(silent=True)
    seq.add(nop, complete_on=obj.listener, name="timeout step", check_timeout=2)
    seq.add(lambda: test_res.append(2))
    seq.add(nop, name="after listener step")

    def check_res():
        assert test_res == [0, 1, 2]

    seq.add(check_res)

    seq.done()
    obj.listener()

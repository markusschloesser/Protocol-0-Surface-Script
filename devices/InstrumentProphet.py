from typing import Any, Optional

from protocol0.devices.AbstractInstrument import AbstractInstrument
from protocol0.enums.ColorEnum import ColorEnum
from protocol0.sequence.Sequence import Sequence


class InstrumentProphet(AbstractInstrument):
    NAME = "Prophet"
    DEVICE_NAME = "rev2editor"
    TRACK_COLOR = ColorEnum.PROPHET
    IS_EXTERNAL_SYNTH = True
    ACTIVE_INSTANCE = None  # type: Optional[InstrumentProphet]

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(InstrumentProphet, self).__init__(*a, **k)

    @property
    def needs_exclusive_activation(self):
        # type: () -> bool
        return InstrumentProphet.ACTIVE_INSTANCE != self

    def exclusive_activate(self):
        # type: () -> Optional[Sequence]
        InstrumentProphet.ACTIVE_INSTANCE = self
        seq = Sequence()
        seq.add(self.system.activate_rev2_editor, wait=10)
        return seq.done()

import re

from typing import TYPE_CHECKING, Any, Optional

from protocol0.lom.AbstractObject import AbstractObject
from protocol0.utils.utils import smart_string

if TYPE_CHECKING:
    from protocol0.devices.AbstractInstrument import AbstractInstrument


class InstrumentPreset(AbstractObject):
    def __init__(self, instrument, index, name, category=None, *a, **k):
        # type: (AbstractInstrument, int, Optional[basestring], Optional[str], Any, Any) -> None
        super(InstrumentPreset, self).__init__(*a, **k)
        self.instrument = instrument
        self.index = index
        name = smart_string(name) if name else None
        self.original_name = name
        self.name = self._format_name(name)
        self.category = category.lower() if category else None

    def __repr__(self):
        # type: () -> str
        name = "%s (%s)" % (self.name, self.index + 1)
        if self.category:
            name += "(%s)" % self.category
        return name

    def _format_name(self, name):
        # type: (Optional[str]) -> str
        if not name:
            return "empty"

        base_preset_name = re.sub('\\.[a-z0-9]{2,4}', '', name)  # remove file extension
        return self.instrument.format_preset_name(str(base_preset_name))  # calling subclass formatting

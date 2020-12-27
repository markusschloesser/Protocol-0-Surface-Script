from a_protocol_0.devices.AbstractInstrument import AbstractInstrument
from a_protocol_0.utils.Sequence import Sequence


class InstrumentProphet(AbstractInstrument):
    NEEDS_EXCLUSIVE_ACTIVATION = True

    def exclusive_activate(self):
        # type: () -> Sequence
        self.active_instance = self

        seq = Sequence(interval=1, name="exclusive prophet activation")
        seq.add(self.song.select_track(self.device_track))
        seq.add(self.parent.keyboardShortcutManager.show_and_activate_rev2_editor, name="show_and_activate_rev2_editor")

        return seq

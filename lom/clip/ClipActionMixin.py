from typing import TYPE_CHECKING, Optional

import Live
from protocol0.constants import QUANTIZATION_OPTIONS
from protocol0.lom.device.DeviceParameter import DeviceParameter
from protocol0.sequence.Sequence import Sequence

if TYPE_CHECKING:
    from protocol0.lom.clip.Clip import Clip


# noinspection PyTypeHints
class ClipActionMixin(object):
    @property
    def is_playing(self):
        # type: (Clip) -> bool
        return self._clip and self._clip.is_playing

    @is_playing.setter
    def is_playing(self, is_playing):
        # type: (Clip, bool) -> None
        if self._clip:
            self._clip.is_playing = is_playing

    def select(self):
        # type: (Clip) -> Sequence
        self.song.highlighted_clip_slot = self.clip_slot
        seq = Sequence()
        seq.add(self.parent.navigationManager.show_clip_view)
        return seq.done()

    def stop(self, immediate=False):
        # type: (Clip, bool) -> None
        if immediate:
            self.muted = True
            self.muted = False
            return None

        if self._clip:
            self._clip.stop()

    def fire(self):
        # type: (Clip) -> None
        if self._clip:
            self._clip.fire()

    def delete(self):
        # type: (Clip) -> Sequence
        return self.clip_slot.delete_clip()

    def quantize(self, depth=1):
        # type: (Clip, float) -> None
        if self._clip:
            record_quantization_index = QUANTIZATION_OPTIONS.index(self.song.midi_recording_quantization)
            if record_quantization_index:
                self._clip.quantize(record_quantization_index, depth)

    def automation_envelope(self, parameter):
        # type: (Clip, DeviceParameter) -> Live.Clip.AutomationEnvelope
        return self._clip and self._clip.automation_envelope(parameter._device_parameter)

    def show_loop(self):
        # type: (Clip) -> None
        self.view.show_loop()

    def show_envelope(self):
        # type: (Clip) -> None
        self.hide_envelope()  # necessary
        self.view.show_envelope()

    def hide_envelope(self):
        # type: (Clip) -> None
        self.view.hide_envelope()

    def create_automation_envelope(self, parameter):
        # type: (Clip, DeviceParameter) -> Live.Clip.AutomationEnvelope
        return self._clip.create_automation_envelope(parameter._device_parameter)

    def clear_all_envelopes(self):
        # type: (Clip) -> None
        if self._clip:
            return self._clip.clear_all_envelopes()

    def configure_new_clip(self):
        # type: (Clip) -> Optional[Sequence]
        """ overridden """
        pass

    def refresh_appearance(self):
        # type: (Clip) -> None
        self.clip_name._name_listener(force=True)  # type: ignore[has-type]
        self.color = self.track.computed_color

    def post_record(self):
        # type: (Clip) -> None
        """ overridden """
        self.clip_name.update(base_name="")

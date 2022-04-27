from __future__ import division

from functools import partial

import Live
from typing import List, TYPE_CHECKING, Optional, Iterator, cast

from protocol0.domain.lom.clip.Clip import Clip
from protocol0.domain.lom.device_parameter.LinkedDeviceParameters import LinkedDeviceParameters
from protocol0.domain.lom.note.Note import Note
from protocol0.domain.shared.errors.Protocol0Warning import Protocol0Warning
from protocol0.domain.shared.utils import find_if
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.SongViewFacade import SongViewFacade
from protocol0.shared.sequence.Sequence import Sequence

if TYPE_CHECKING:
    from protocol0.domain.lom.clip_slot.MidiClipSlot import MidiClipSlot  # noqa


class MidiClip(Clip):
    def __init__(self, clip_slot):
        # type: (MidiClipSlot) -> None
        super(MidiClip, self).__init__(clip_slot)
        from protocol0.domain.lom.track.simple_track.SimpleMidiTrack import SimpleMidiTrack
        from protocol0.domain.lom.clip_slot.MidiClipSlot import MidiClipSlot  # noqa

        self.track = cast(SimpleMidiTrack, self.track)
        self.clip_slot = cast(MidiClipSlot, self.clip_slot)
        # NOTES
        self._cached_notes = []  # type: List[Note]

    def hash(self):
        # type: () -> int
        return hash(tuple(note.to_data() for note in self.get_notes()))

    def get_notes(self):
        # type: () -> List[Note]
        if not self._clip:
            return []
        # noinspection PyArgumentList
        clip_notes = [Note(*note) for note in self._clip.get_notes(self.loop_start, 0, self.length, 128)]
        notes = list(self._get_notes_from_cache(notes=clip_notes))
        notes.sort(key=lambda x: x.start)
        return notes

    def _get_notes_from_cache(self, notes):
        # type: (List[Note]) -> Iterator[Note]
        for note in notes:
            yield next((cached_note for cached_note in self._cached_notes if cached_note == note), note)

    def set_notes(self, notes):
        # type: (List[Note]) -> Optional[Sequence]
        if not self._clip:
            return None
        self._cached_notes = notes
        self._clip.select_all_notes()
        seq = Sequence()
        seq.add(partial(self._clip.replace_selected_notes, tuple(note.to_data() for note in notes)))
        # noinspection PyUnresolvedReferences
        seq.defer()
        return seq.done()

    def configure_new_clip(self):
        # type: () -> Optional[Sequence]
        if len(self.get_notes()) > 0 or self.is_recording:
            return None

        self.view.grid_quantization = Live.Clip.GridQuantization.g_sixteenth
        seq = Sequence()
        seq.defer()
        seq.add(self.generate_base_notes)
        seq.wait(10)
        return seq.done()

    def generate_base_notes(self):
        # type: () -> Optional[Sequence]
        if self.track.instrument:
            if self.track.instrument.uses_scene_length_clips:
                self.bar_length = SongFacade.selected_scene().bar_length
                self.show_loop()

            pitch = self.track.instrument.DEFAULT_NOTE
            base_notes = [Note(pitch=pitch, velocity=127, start=0, duration=min(1, int(self.length)))]
            return self.set_notes(base_notes)
        else:
            return None

    def post_record(self, bar_length):
        # type: (int) -> None
        super(MidiClip, self).post_record(bar_length)
        if bar_length == 0:  # unlimited recording
            clip_end = int(self.end_marker) - (int(self.end_marker) % SongFacade.signature_numerator())
            self.loop_end = clip_end
            self.end_marker = clip_end

        self.view.grid_quantization = Live.Clip.GridQuantization.g_sixteenth
        self.scale_velocities(go_next=False, scaling_factor=2)
        self.quantize()

    def scale_velocities(self, go_next, scaling_factor=4):
        # type: (bool, int) -> None
        notes = self.get_notes()
        if len(notes) == 0:
            return
        average_velo = sum([note.velocity for note in notes]) / len(notes)
        for note in notes:
            velocity_diff = note.velocity - average_velo
            if go_next:
                note.velocity += velocity_diff / (scaling_factor - 1)
            else:
                note.velocity -= velocity_diff / scaling_factor
        self.set_notes(notes)

    def crop(self):
        # type: () -> None
        if self._clip:
            self._clip.crop()

    def get_linked_parameters(self):
        # type: () -> List[LinkedDeviceParameters]
        """
            NB : this is only really useful for my rev2 where I want to copy and paste easily automation curves
            between the 2 layers.
            The rev2 is bitimbral and has two layers that expose the same parameters.
        """
        parameters = self.automated_parameters
        parameters_couple = []
        for parameter in parameters:
            if parameter.name.startswith("A-"):
                b_parameter = find_if(lambda p: p.name == parameter.name.replace("A-", "B-"), parameters)
                if b_parameter:
                    parameters_couple.append(LinkedDeviceParameters(parameter, b_parameter))

        return parameters_couple

    def synchronize_automation_layers(self):
        # type: () -> Sequence
        parameters_couple = self.get_linked_parameters()
        if len(parameters_couple) == 0:
            raise Protocol0Warning("This clip has no linked automated parameters")

        SongViewFacade.draw_mode(False)
        seq = Sequence()
        for couple in parameters_couple:
            seq.add(partial(couple.link_clip_automation, self))

        # refocus an A parameter to avoid mistakenly modify a B one
        seq.add(partial(self.show_parameter_envelope, parameters_couple[-1]._param_a))

        return seq.done()

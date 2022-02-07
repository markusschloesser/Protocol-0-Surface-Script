from functools import partial

from typing import Optional

from protocol0.domain.lom.Listenable import Listenable
from protocol0.domain.lom.track.group_track.ExternalSynthTrack import ExternalSynthTrack
from protocol0.domain.lom.track.routing.InputRoutingTypeEnum import InputRoutingTypeEnum
from protocol0.domain.sequence.Sequence import Sequence
from protocol0.domain.shared.BeatChangedEvent import BeatChangedEvent
from protocol0.domain.shared.DomainEventBus import DomainEventBus
from protocol0.domain.shared.Last32thPassedEvent import Last32thPassedEvent
from protocol0.domain.shared.decorators import p0_subject_slot
from protocol0.domain.track_recorder.decorator.track_recorder_decorator import TrackRecorderDecorator
from protocol0.domain.track_recorder.recorder.abstract_track_recorder import AbstractTrackRecorder


class TrackRecorderClipTailDecorator(TrackRecorderDecorator, Listenable):
    __subject_events__ = ("is_silent",)

    def __init__(self, recorder):
        # type: (AbstractTrackRecorder) -> None
        super(TrackRecorderClipTailDecorator, self).__init__(recorder=recorder)
        self._is_silent_listener.subject = self

    @property
    def track(self):
        # type: (AbstractTrackRecorder) -> ExternalSynthTrack
        # noinspection PyTypeChecker
        return self._track

    def _beat_changed_listener(self, _):
        # type: (BeatChangedEvent) -> None
        if self.is_audio_silent:
            # noinspection PyUnresolvedReferences
            self.notify_is_silent()

    @property
    def is_audio_silent(self):
        # type: () -> bool
        return self.track.audio_tail_track.output_meter_left < 0.1

    @p0_subject_slot("is_silent")
    def _is_silent_listener(self):
        # type: () -> None
        pass

    def post_audio_record(self):
        # type: () -> Optional[Sequence]
        super(TrackRecorderClipTailDecorator, self).post_audio_record
        if self.is_audio_silent:
            return None
        else:
            seq = Sequence()
            seq.add(self._wait_for_clip_tail_end)
            return seq.done()

    def _wait_for_clip_tail_end(self):
        # type: () -> Sequence
        input_routing_type = self.track.midi_track.input_routing.type

        audio_clip = self.track.audio_track.clip_slots[self.recording_scene_index].clip
        audio_clip.fire()
        DomainEventBus.subscribe(BeatChangedEvent, self._beat_changed_listener)

        # following is a trick to have no midi note input at the very end of the bar while being able
        # to still record automation
        # This combined with the last_32th_listener will record parameter automation in the midi clip
        # almost perfectly until the end of the bar while having no notes playing when the tail starts recording
        midi_clip = self.track.midi_track.clip_slots[self.recording_scene_index].clip
        midi_notes = midi_clip.get_notes()
        for note in midi_notes:
            note.muted = True
        midi_clip.set_notes(midi_notes)
        for note in midi_notes:
            note.muted = False

        seq = Sequence()
        # so that we have automation until the very end
        seq.add(wait_for_event=Last32thPassedEvent)
        seq.add(partial(setattr, self._song, "session_automation_record", False))
        seq.add(partial(self.track.midi_track.stop, immediate=True))
        seq.add(partial(setattr, self.track.midi_track.input_routing, "type", InputRoutingTypeEnum.NO_INPUT))
        seq.add(wait_beats=1)
        seq.add(partial(midi_clip.set_notes, midi_notes))
        seq.add(complete_on=self._is_silent_listener, no_timeout=True)
        seq.add(partial(setattr, self.track.midi_track.input_routing, "type", input_routing_type))
        seq.add(partial(DomainEventBus.un_subscribe, BeatChangedEvent, self._beat_changed_listener))
        return seq.done()

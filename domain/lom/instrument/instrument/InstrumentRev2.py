from typing import Optional, Any

from protocol0.domain.lom.device.DeviceEnum import DeviceEnum
from protocol0.domain.lom.instrument.InstrumentColorEnum import InstrumentColorEnum
from protocol0.domain.lom.instrument.InstrumentInterface import InstrumentInterface
from protocol0.domain.lom.track.simple_track.SimpleTrackArmedEvent import SimpleTrackArmedEvent
from protocol0.domain.shared.backend.Backend import Backend
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.domain.track_recorder.external_synth.ExternalSynthAudioRecordingEndedEvent import (
    ExternalSynthAudioRecordingEndedEvent,
)
from protocol0.domain.track_recorder.external_synth.ExternalSynthAudioRecordingStartedEvent import (
    ExternalSynthAudioRecordingStartedEvent,
)
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.sequence.Sequence import Sequence


class InstrumentRev2(InstrumentInterface):
    NAME = "Rev2"
    DEVICE = DeviceEnum.REV2_EDITOR
    TRACK_COLOR = InstrumentColorEnum.REV2
    INSTRUMENT_TRACK_NAME = "Synth"
    ACTIVE_INSTANCE = None  # type: Optional[InstrumentRev2]
    IS_EXTERNAL_SYNTH = True

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(InstrumentRev2, self).__init__(*a, **k)

        self.force_show = True

        DomainEventBus.subscribe(SimpleTrackArmedEvent, self._on_simple_track_armed_event)
        DomainEventBus.subscribe(
            ExternalSynthAudioRecordingStartedEvent, self._on_audio_recording_started_event
        )
        DomainEventBus.subscribe(
            ExternalSynthAudioRecordingEndedEvent, self._on_audio_recording_ended_event
        )

    @property
    def needs_exclusive_activation(self):
        # type: () -> bool
        return InstrumentRev2.ACTIVE_INSTANCE != self

    def exclusive_activate(self):
        # type: () -> Optional[Sequence]
        InstrumentRev2.ACTIVE_INSTANCE = self
        seq = Sequence()
        seq.wait(5)
        seq.add(Backend.client().activate_rev2_editor)
        seq.wait(10)
        return seq.done()

    def post_activate(self):
        # type: () -> Optional[Sequence]
        seq = Sequence()
        seq.add(Backend.client().post_activate_rev2_editor)
        seq.wait(25)
        return seq.done()

    def _on_simple_track_armed_event(self, event):
        # type: (SimpleTrackArmedEvent) -> None
        """because rev2 midi is generated by the rev2 editor"""
        track = SongFacade.simple_track_from_live_track(event.live_track)

        if track.instrument != self:
            return

        self.device.is_enabled = True

    def _on_audio_recording_started_event(self, event):
        # type: (ExternalSynthAudioRecordingStartedEvent) -> None
        if event.track.instrument != self:
            return
        # self.device.is_enabled = False

    def _on_audio_recording_ended_event(self, event):
        # type: (ExternalSynthAudioRecordingEndedEvent) -> None
        if event.track.instrument != self:
            return

        # self.device.is_enabled = True

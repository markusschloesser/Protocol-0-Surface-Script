from functools import partial

from typing import Optional

from protocol0.domain.lom.track.abstract_track.AbstrackTrackArmState import AbstractTrackArmState
from protocol0.domain.lom.track.group_track.external_synth_track.ExternalSynthTrackArmedEvent import \
    ExternalSynthTrackArmedEvent
from protocol0.domain.lom.track.routing.InputRoutingTypeEnum import InputRoutingTypeEnum
from protocol0.domain.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
from protocol0.domain.lom.track.simple_track.SimpleMidiTrack import SimpleMidiTrack
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.shared.sequence.Sequence import Sequence


class ExternalSynthTrackArmState(AbstractTrackArmState):
    def __init__(self, base_track, midi_track):
        # type: (SimpleAudioTrack, SimpleMidiTrack) -> None
        super(ExternalSynthTrackArmState, self).__init__(base_track._track)
        self._base_track = base_track
        self._sub_tracks = base_track.sub_tracks
        self._midi_track = midi_track

    @property
    def is_armed(self):
        # type: () -> bool
        return all(
            sub_track.arm_state.is_armed
            for sub_track in self._sub_tracks
        )

    @is_armed.setter
    def is_armed(self, is_armed):
        # type: (bool) -> None
        for track in self._sub_tracks:
            track.arm_state.is_armed = is_armed

    @property
    def is_partially_armed(self):
        # type: () -> bool
        return any(
            sub_track.arm_state.is_armed
            for sub_track in self._sub_tracks
        )

    def arm_track(self):
        # type: () -> Optional[Sequence]
        self._base_track.is_folded = False
        self._base_track.muted = False

        if self._midi_track.input_routing.type == InputRoutingTypeEnum.NO_INPUT:
            self._midi_track.input_routing.type = InputRoutingTypeEnum.ALL_INS

        seq = Sequence()
        seq.add(
            [
                sub_track.arm_state.arm_track
                for sub_track in self._sub_tracks
            ]
        )
        seq.add(self.notify_observers)
        seq.add(partial(DomainEventBus.emit, ExternalSynthTrackArmedEvent(self._base_track)))
        return seq.done()

    def unarm(self):
        # type: () -> None
        self.is_armed = False

        DomainEventBus.emit(ExternalSynthTrackArmedEvent(self._base_track, arm=False))
        self.notify_observers()

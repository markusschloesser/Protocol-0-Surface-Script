from typing import Optional

from protocol0.domain.lom.device.Device import Device
from protocol0.domain.lom.track.CurrentMonitoringStateEnum import CurrentMonitoringStateEnum
from protocol0.domain.lom.track.MonitoringStateInterface import MonitoringStateInterface
from protocol0.domain.lom.track.group_track.dummy_group.DummyGroup import DummyGroup
from protocol0.domain.lom.track.group_track.external_synth_track.ExternalSynthMatchingTrack import \
    ExternalSynthMatchingTrack
from protocol0.domain.lom.track.group_track.external_synth_track.ExternalSynthTrackArmState import \
    ExternalSynthTrackArmState
from protocol0.domain.lom.track.routing.OutputRoutingTypeEnum import OutputRoutingTypeEnum
from protocol0.domain.lom.track.simple_track.SimpleAudioTailTrack import SimpleAudioTailTrack
from protocol0.domain.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
from protocol0.domain.lom.track.simple_track.SimpleMidiTrack import SimpleMidiTrack
from protocol0.domain.lom.track.simple_track.SimpleTrack import SimpleTrack
from protocol0.domain.shared.errors.Protocol0Warning import Protocol0Warning
from protocol0.shared.observer.Observable import Observable


class ExternalSynthTrackMonitoringState(MonitoringStateInterface):
    def __init__(
        self,
        midi_track,  # type: SimpleMidiTrack
        audio_track,  # type: SimpleAudioTrack
        audio_tail_track,  # type: Optional[SimpleAudioTailTrack]
        dummy_group,  # type: DummyGroup
        matching_track,  # type: ExternalSynthMatchingTrack
        external_device,  # type: Device
    ):
        # type: (...) -> None
        self._midi_track = midi_track
        self._audio_track = audio_track
        self._audio_tail_track = audio_tail_track
        self._dummy_group = dummy_group
        self._matching_track = matching_track
        self.external_device = external_device

    def update(self, observable):
        # type: (Observable) -> None
        if isinstance(observable, ExternalSynthTrackArmState):
            if observable.is_armed:
                self.monitor_midi()
            else:
                self.monitor_audio()

    def set_audio_tail_track(self, track):
        # type: (Optional[SimpleAudioTailTrack]) -> None
        """Track is not mapped on __ini__"""
        self._audio_tail_track = track

    def switch(self):
        # type: () -> None
        if self._matching_track.exists:
            self._matching_track.switch_monitoring()
            return

        if self._monitors_midi:
            self.monitor_audio()
        else:
            if self._midi_track.arm_state.is_armed:
                self.monitor_midi()
            else:
                raise Protocol0Warning("Please arm the track first")

    @property
    def _monitors_midi(self):
        # type: () -> bool
        return not self._midi_track.muted

    def monitor_midi(self):
        # type: () -> None
        # midi track
        self._un_mute_track(self._midi_track)

        # audio track
        self._mute_track(self._audio_track)
        self._audio_track._output_meter_level_listener.subject = self._audio_track._track

        # audio tail track
        if self._audio_tail_track:
            self._mute_track(self._audio_tail_track)

        # switch solo
        if self._audio_track.solo:
            self._midi_track.solo = True
            self._audio_track.solo = False

        # external device
        self.external_device.is_enabled = True

    # noinspection DuplicatedCode
    def monitor_audio(self):
        # type: () -> None
        # midi track
        self._midi_track.muted = True
        self._midi_track.current_monitoring_state = CurrentMonitoringStateEnum.OFF
        self._midi_track.output_routing.type = OutputRoutingTypeEnum.SENDS_ONLY

        # audio track
        self._un_mute_track(self._audio_track)
        self._audio_track._output_meter_level_listener.subject = None

        # audio tail track
        if self._audio_tail_track:
            self._un_mute_track(self._audio_tail_track)

        # switch solo
        if self._midi_track.solo:
            self._audio_track.solo = True
            self._midi_track.solo = False

        # external device
        self.external_device.is_enabled = False

    def _mute_track(self, track):
        # type: (SimpleTrack) -> None
        track.muted = True
        track.current_monitoring_state = CurrentMonitoringStateEnum.IN
        track.output_routing.type = OutputRoutingTypeEnum.SENDS_ONLY

    def _un_mute_track(self, track):
        # type: (SimpleTrack) -> None
        track.muted = False
        track.current_monitoring_state = CurrentMonitoringStateEnum.AUTO
        track.output_routing.track = self._dummy_group.input_routing_track

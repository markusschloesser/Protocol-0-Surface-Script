from functools import partial

from typing import List, Any, cast, Optional

from protocol0.domain.lom.clip.DummyClip import DummyClip
from protocol0.domain.lom.clip_slot.DummyClipSlot import DummyClipSlot
from protocol0.domain.lom.device_parameter.DeviceParameter import DeviceParameter
from protocol0.domain.lom.track.CurrentMonitoringStateEnum import CurrentMonitoringStateEnum
from protocol0.domain.lom.track.abstract_track.AbstractTrack import AbstractTrack
from protocol0.domain.lom.track.routing.InputRoutingTypeEnum import InputRoutingTypeEnum
from protocol0.domain.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
from protocol0.domain.lom.track.simple_track.SimpleDummyTrackAddedEvent import (
    SimpleDummyTrackAddedEvent,
)
from protocol0.domain.lom.track.simple_track.SimpleDummyTrackAutomation import (
    SimpleDummyTrackAutomation,
)
from protocol0.domain.lom.track.simple_track.SimpleTrackClipSlots import SimpleTrackClipSlots
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.domain.shared.scheduler.Scheduler import Scheduler
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.observer.Observable import Observable


class SimpleDummyTrack(SimpleAudioTrack):
    CLIP_SLOT_CLASS = DummyClipSlot
    TRACK_NAME = "d"

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(SimpleAudioTrack, self).__init__(*a, **k)

        self._clip_slots.register_observer(self)

        self.automation = SimpleDummyTrackAutomation(self._track, self._clip_slots, self.devices)
        if self.name != self.TRACK_NAME:
            Scheduler.defer(partial(setattr, self, "name", self.TRACK_NAME))

    def update(self, observable):
        # type: (Observable) -> None
        # manually setting the has_automation attribute
        if isinstance(observable, SimpleTrackClipSlots):
            for clip in self.clips:
                clip.has_automation = (
                    len(clip.automation.get_automated_parameters(self.devices.parameters)) != 0
                )

    @classmethod
    def is_track_valid(cls, track):
        # type: (AbstractTrack) -> bool
        if isinstance(track, SimpleDummyTrack):
            return True

        # we don't accept specialized subclasses as we expect a non mapped class (e.g. no tail)
        # if input routing is not no input, we consider a normal audio track (could be a doubling track)
        return (
            type(track) == SimpleAudioTrack
            and not track.is_foldable
            and track.instrument is None
            and track.input_routing.type == InputRoutingTypeEnum.NO_INPUT
        )

    @property
    def clip_slots(self):
        # type: () -> List[DummyClipSlot]
        return cast(List[DummyClipSlot], super(SimpleDummyTrack, self).clip_slots)

    @property
    def clips(self):
        # type: () -> List[DummyClip]
        return cast(List[DummyClip], super(SimpleDummyTrack, self).clips)

    def on_added(self):
        # type: () -> None
        self.current_monitoring_state = CurrentMonitoringStateEnum.IN
        self.input_routing.type = InputRoutingTypeEnum.NO_INPUT
        super(SimpleDummyTrack, self).on_added()
        DomainEventBus.emit(SimpleDummyTrackAddedEvent(self._track))

    def prepare_automation_for_clip_start(self, dummy_clip):
        # type: (DummyClip) -> None
        """
        This will set automation values to equal the clip start
        It is used to prevent automation glitches when a track starts playing after silence
        """
        clip_parameters = dummy_clip.automation.get_automated_parameters(self.devices.parameters)

        for parameter in clip_parameters:
            envelope = dummy_clip.automation.get_envelope(parameter)
            # we don't take value_at_time(0) because we often have 2 points at zero,
            # the first one being wrong
            parameter.value = round(envelope.value_at_time(0.000001), 3)

    def get_stopping_automated_parameters(self, scene_index, next_scene_index):
        # type: (int, Optional[int]) -> List[DeviceParameter]
        dummy_clip = self.clip_slots[scene_index].clip
        parameters = dummy_clip.automation.get_automated_parameters(self.devices.parameters)

        next_parameters = []  # type: List[DeviceParameter]
        if next_scene_index is not None:
            next_dummy_clip = self.clip_slots[next_scene_index].clip
            if next_dummy_clip is not None:
                next_parameters = next_dummy_clip.automation.get_automated_parameters(
                    self.devices.parameters
                )

        return list(set(parameters) - set(next_parameters))

    def reset_automated_parameters(self, scene_index):
        # type: (int) -> None
        """
        This executes at the start of each scene and resets automation previously defined
        (minus the one defined in the optional playing clip)
        Doing this is useful because automation using dummy clips is always specific to the clip
        as opposed to doing it in arrangement (it's a whole)
        and the parameter will stay at the same value when the clip stops which is not
        the behavior we seek here
        """
        next_scene_index = None
        if SongFacade.is_playing() and self.is_playing:
            next_scene_index = self.playing_clip.index

        for parameter in self.get_stopping_automated_parameters(scene_index, next_scene_index):
            parameter.reset()

    def reset_all_automated_parameters(self):
        # type: () -> None
        """Will reset all automated parameters in the track by checking all dummy clips"""
        parameters = {}
        for dummy_clip in self.clips:
            parameters.update(self.get_automated_parameters(dummy_clip.index))

        for parameter in parameters:
            parameter.reset()

    @property
    def computed_color(self):
        # type: () -> int
        return self.group_track.appearance.color

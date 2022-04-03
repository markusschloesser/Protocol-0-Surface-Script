from itertools import chain

import Live
from typing import List, Optional

from protocol0.domain.lom.clip_slot.ClipSlot import ClipSlot
from protocol0.domain.lom.device.Device import Device
from protocol0.domain.lom.device_parameter.DeviceParameter import DeviceParameter
from protocol0.domain.lom.instrument.InstrumentFactory import InstrumentFactory
from protocol0.domain.lom.instrument.InstrumentInterface import InstrumentInterface
from protocol0.domain.lom.track.CurrentMonitoringStateEnum import CurrentMonitoringStateEnum
from protocol0.domain.lom.track.abstract_track.AbstractTrack import AbstractTrack
from protocol0.domain.lom.track.simple_track.SimpleTrackActionMixin import SimpleTrackActionMixin
from protocol0.domain.lom.track.simple_track.SimpleTrackCreatedEvent import SimpleTrackCreatedEvent
from protocol0.domain.shared.DomainEventBus import DomainEventBus
from protocol0.domain.shared.decorators import p0_subject_slot
from protocol0.domain.shared.utils import find_if
from protocol0.shared.Config import Config
from protocol0.shared.SongFacade import SongFacade


class SimpleTrack(SimpleTrackActionMixin, AbstractTrack):
    # is_active is used to differentiate set tracks for return / master
    # we act only on active tracks
    IS_ACTIVE = True
    CLIP_SLOT_CLASS = ClipSlot

    def __init__(self, track, index):
        # type: (Live.Track.Track, int) -> None
        self._track = track  # type: Live.Track.Track
        self._index = index
        super(SimpleTrack, self).__init__(track=self)
        # Note : SimpleTracks represent the first layer of abstraction and know nothing about
        # AbstractGroupTracks except with self.abstract_group_track which links both layers
        # and is handled by the abg
        self.group_track = self.group_track  # type: Optional[SimpleTrack]
        self.sub_tracks = []  # type: List[SimpleTrack]

        self.devices = []  # type: List[Device]
        self.all_devices = []  # type: List[Device]
        self._instrument = None  # type: Optional[InstrumentInterface]
        self.clip_slots = []  # type: List[ClipSlot]
        self._map_clip_slots()

        self._devices_listener.subject = self._track
        self._devices_listener()

        self._output_meter_level_listener.subject = None

        DomainEventBus.notify(SimpleTrackCreatedEvent(self))

    @property
    def live_id(self):
        # type: () -> int
        return self._track._live_ptr

    @property
    def is_active(self):
        # type: () -> bool
        return self._track not in list(self._song._song.return_tracks) + [self._song._song.master_track]

    def on_tracks_change(self):
        # type: () -> None
        self._link_to_group_track()
        # because we traverse the tracks left to right : sub tracks will register themselves
        if self.is_foldable:
            self.sub_tracks[:] = []

    def on_scenes_change(self):
        # type: () -> None
        self._map_clip_slots()

    def _link_to_group_track(self):
        # type: () -> None
        """
            1st layer linking
            Connect to the enclosing simple group track is any
        """
        if self._track.group_track is None:
            self.group_track = None
            return None

        self.group_track = SongFacade.simple_track_from_live_track(self._track.group_track)
        self.group_track.add_or_replace_sub_track(self)

    def _map_clip_slots(self):
        # type: () -> None
        """ create new ClipSlot objects and keep existing ones """
        live_cs_to_cs = {cs._clip_slot: cs for cs in self.clip_slots}

        new_clip_slots = []  # type: List[ClipSlot]
        for (i, clip_slot) in enumerate(list(self._track.clip_slots)):
            if clip_slot in live_cs_to_cs:
                new_clip_slots.append(live_cs_to_cs[clip_slot])
            else:
                new_clip_slots.append(ClipSlot.make(clip_slot=clip_slot, track=self))
        self.clip_slots[:] = new_clip_slots  # type: List[ClipSlot]

    def refresh_appearance(self):
        # type: (SimpleTrack) -> None
        super(SimpleTrack, self).refresh_appearance()
        for clip_slot in self.clip_slots:
            clip_slot.refresh_appearance()

    @p0_subject_slot("devices")
    def _devices_listener(self):
        # type: () -> None
        for device in self.devices:
            device.disconnect()

        self.devices = [Device.make(device, self) for device in self._track.devices]

        self.all_devices = self._find_all_devices(self.base_track)

        # noinspection PyUnresolvedReferences
        self.notify_devices()

        # Refreshing is only really useful from simpler devices that change when a new sample is loaded
        if self.IS_ACTIVE and not self.is_foldable:
            self.instrument = InstrumentFactory.make_instrument_from_simple_track(track=self)
            # if self.instrument:
            #     self.abstract_track.refresh_appearance()

    @p0_subject_slot("output_meter_level")
    def _output_meter_level_listener(self):
        # type: () -> None
        if self.output_meter_level > Config.CLIPPING_TRACK_VOLUME:
            # some clicks e.g. when starting / stopping the song have this value
            if round(self.output_meter_level, 3) == 0.921:
                return
            # Backend.client().show_warning("%s is clipping (%.3f)" % (self.abstract_track.name, self.output_meter_level))

    @property
    def is_armed(self):
        # type: () -> bool
        return self._track and self.can_be_armed and self._track.arm

    @is_armed.setter
    def is_armed(self, is_armed):
        # type: (bool) -> None
        if self.can_be_armed and self._track:
            self._track.arm = is_armed

    @property
    def is_armable(self):
        # type: () -> bool
        """ Checks for disabled input routing """
        if not self.can_be_armed:
            return True
        self.is_armed = True
        if self.is_armed:
            self.is_armed = False
            return True
        else:
            return False

    @property
    def current_monitoring_state(self):
        # type: () -> CurrentMonitoringStateEnum
        if self._track is None:
            return CurrentMonitoringStateEnum.AUTO
        return CurrentMonitoringStateEnum.from_value(self._track.current_monitoring_state)

    @current_monitoring_state.setter
    def current_monitoring_state(self, monitoring_state):
        # type: (CurrentMonitoringStateEnum) -> None
        if self._track:
            self._track.current_monitoring_state = monitoring_state.value

    @property
    def output_meter_left(self):
        # type: () -> float
        return self._track.output_meter_left if self._track else 0

    @property
    def playing_slot_index(self):
        # type: () -> int
        return self._track.playing_slot_index if self._track else 0

    @property
    def fired_slot_index(self):
        # type: () -> int
        return self._track.fired_slot_index if self._track else 0

    @property
    def device_parameters(self):
        # type: () -> List[DeviceParameter]
        return list(chain(*[device.parameters for device in self.all_devices]))

    @property
    def instrument(self):
        # type: () -> Optional[InstrumentInterface]
        return self._instrument

    @instrument.setter
    def instrument(self, instrument):
        # type: (InstrumentInterface) -> None
        self._instrument = instrument

    @property
    def is_playing(self):
        # type: () -> bool
        return any(clip_slot.is_playing for clip_slot in self.clip_slots)

    @property
    def is_triggered(self):
        # type: () -> bool
        return any(clip_slot.is_triggered for clip_slot in self.clip_slots)

    @property
    def is_recording(self):
        # type: () -> bool
        return any(clip for clip in self.clips if clip and clip.is_recording)

    @property
    def selected_device(self):
        # type: (SimpleTrack) -> Optional[Device]
        if self._track and self._track.view.selected_device:
            device = find_if(
                lambda d: d._device == self._track.view.selected_device, self.base_track.all_devices
            )  # type: Optional[Device]
            assert device
            return device
        else:
            return None

    def disconnect(self):
        # type: () -> None
        super(SimpleTrack, self).disconnect()
        for device in self.devices:
            device.disconnect()
        for clip_slot in self.clip_slots:
            clip_slot.disconnect()

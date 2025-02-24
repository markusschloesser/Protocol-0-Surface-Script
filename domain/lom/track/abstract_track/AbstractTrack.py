from functools import partial

import Live
from _Framework.SubjectSlot import SlotManager
from typing import Optional, List, Iterator, cast, TYPE_CHECKING, Dict

from protocol0.domain.lom.clip.Clip import Clip
from protocol0.domain.lom.clip.ClipSlotSelectedEvent import ClipSlotSelectedEvent
from protocol0.domain.lom.clip_slot.ClipSlot import ClipSlot
from protocol0.domain.lom.device_parameter.DeviceParameter import DeviceParameter
from protocol0.domain.lom.instrument.InstrumentInterface import InstrumentInterface
from protocol0.domain.lom.track.MonitoringStateInterface import MonitoringStateInterface
from protocol0.domain.lom.track.TrackColorEnum import TrackColorEnum
from protocol0.domain.lom.track.abstract_track.AbstrackTrackArmState import AbstractTrackArmState
from protocol0.domain.lom.track.abstract_track.AbstractMatchingTrack import AbstractMatchingTrack
from protocol0.domain.lom.track.abstract_track.AbstractTrackAppearance import (
    AbstractTrackAppearance,
)
from protocol0.domain.lom.track.abstract_track.AbstractTrackSelectedEvent import (
    AbstractTrackSelectedEvent,
)
from protocol0.domain.lom.track.routing.TrackInputRouting import TrackInputRouting
from protocol0.domain.lom.track.routing.TrackOutputRouting import TrackOutputRouting
from protocol0.domain.lom.track.simple_track.SimpleTrackMonitoringState import (
    SimpleTrackMonitoringState,
)
from protocol0.domain.shared.ApplicationViewFacade import ApplicationViewFacade
from protocol0.domain.shared.backend.Backend import Backend
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.domain.shared.scheduler.Scheduler import Scheduler
from protocol0.domain.shared.utils.forward_to import ForwardTo
from protocol0.domain.shared.utils.utils import volume_to_db, db_to_volume
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.logging.StatusBar import StatusBar
from protocol0.shared.sequence.Sequence import Sequence

if TYPE_CHECKING:
    from protocol0.domain.lom.track.simple_track.SimpleTrack import SimpleTrack
    from protocol0.domain.lom.track.group_track.AbstractGroupTrack import AbstractGroupTrack


class AbstractTrack(SlotManager):
    # when the color cannot be matched
    REMOVE_CLIPS_ON_ADDED = False
    DEFAULT_COLOR = None  # type: Optional[TrackColorEnum]

    def __init__(self, track):
        # type: (SimpleTrack) -> None
        super(AbstractTrack, self).__init__()
        # TRACKS
        self._track = track._track  # type: Live.Track.Track
        self.base_track = track  # type: SimpleTrack
        self.group_track = None  # type: Optional[AbstractTrack]
        # NB : .group_track is simple for simple tracks and abg for abg tracks
        self.abstract_group_track = None  # type: Optional[AbstractGroupTrack]
        self.sub_tracks = []  # type: List[AbstractTrack]

        # MISC
        self.arm_state = AbstractTrackArmState(self._track)  # type: AbstractTrackArmState
        self.appearance = AbstractTrackAppearance(self._track, self.DEFAULT_COLOR)
        self.input_routing = TrackInputRouting(self.base_track._track)
        self.output_routing = TrackOutputRouting(self.base_track._track)
        self.monitoring_state = SimpleTrackMonitoringState(self)  # type: MonitoringStateInterface

        self.protected_mode_active = True

    def __repr__(self):
        # type: () -> str
        return "%s : %s (%s)" % (self.__class__.__name__, self.name, self.index + 1)

    def __iter__(self):
        # type: () -> Iterator[AbstractTrack]
        return iter(self.sub_tracks)

    def on_added(self):
        # type: () -> Optional[Sequence]
        if self.group_track is not None:
            if self.group_track.color != self.color:
                self.color = self.group_track.color

        if hasattr(self, "matching_track") and issubclass(
            self.matching_track.__class__, AbstractMatchingTrack
        ):
            Scheduler.defer(self.matching_track.connect_base_track)

            if not SongFacade.is_track_recording():
                return self.arm_state.arm()

        return None

    def on_tracks_change(self):
        # type: () -> None
        pass

    def on_scenes_change(self):
        # type: () -> None
        pass

    @property
    def index(self):
        # type: () -> int
        return self.base_track._index

    @property
    def abstract_track(self):
        # type: () -> AbstractTrack
        """
        For top level SimpleTracks, will return self
        For AbstractGroupTracks, will return self (NormalGroupTrack and ExternalSynthTrack)
        Only for nested SimpleTracks, will return their abstract_group_track
        """
        if self.abstract_group_track:
            return self.abstract_group_track
        else:
            return self

    @property
    def group_tracks(self):
        # type: () -> List[AbstractGroupTrack]
        if not self.group_track:
            return []
        return [self.group_track.abstract_track] + self.group_track.group_tracks

    def contains_track(self, track):
        # type: (AbstractTrack) -> bool
        """check if self contains track as a direct or nested sub track"""
        right_most_track = self
        while len(right_most_track.sub_tracks) > 1:
            right_most_track = right_most_track.sub_tracks[-1]

        return self.index <= track.index <= right_most_track.index

    @property
    def instrument_track(self):
        # type: () -> SimpleTrack
        assert self.instrument, "track has not instrument"
        return self.base_track

    def get_view_track(self, scene_index):
        # type: (int) -> Optional[SimpleTrack]
        """Depending on the current view returns the appropriate track"""
        return self.base_track

    @property
    def instrument(self):
        # type: () -> Optional[InstrumentInterface]
        return None

    @property
    def clip_slots(self):
        # type: () -> List[ClipSlot]
        raise NotImplementedError

    @property
    def selected_clip_slot(self):
        # type: () -> Optional[ClipSlot]
        return self.clip_slots[SongFacade.selected_scene().index]

    def select_clip_slot(self, clip_slot):
        # type: (ClipSlot) -> None
        assert clip_slot in [cs for cs in self.clip_slots], "clip slot inconsistency"
        self.is_folded = False
        DomainEventBus.emit(ClipSlotSelectedEvent(clip_slot._clip_slot))

    @property
    def clips(self):
        # type: () -> List[Clip]
        return [
            clip_slot.clip for clip_slot in self.clip_slots if clip_slot.has_clip and clip_slot.clip
        ]

    def has_same_clips(self, track):
        # type: (AbstractTrack) -> bool
        return False

    def clear_clips(self):
        # type: () -> Sequence
        seq = Sequence()
        if self.is_foldable:
            for sub_track in self.sub_tracks:
                seq.add(sub_track.clear_clips)
        else:
            seq.add([clip.delete for clip in self.clips])

        return seq.done()

    name = cast(str, ForwardTo("appearance", "name"))

    @property
    def color(self):
        # type: () -> int
        return self.appearance.color

    @color.setter
    def color(self, color_index):
        # type: (int) -> None
        self.appearance.color = color_index
        for track in self.sub_tracks:
            track.color = color_index
        for clip in self.clips:
            clip.color = color_index

    @property
    def is_foldable(self):
        # type: () -> bool
        return self._track and self._track.is_foldable

    @property
    def is_folded(self):
        # type: () -> bool
        return bool(self._track.fold_state) if self.is_foldable and self._track else True

    @is_folded.setter
    def is_folded(self, is_folded):
        # type: (bool) -> None
        if not is_folded:
            for group_track in self.group_tracks:
                group_track.is_folded = False
        if self._track and self.is_foldable:
            self._track.fold_state = int(is_folded)

    @property
    def solo(self):
        # type: () -> bool
        return self._track and self._track.solo

    @solo.setter
    def solo(self, solo):
        # type: (bool) -> None
        if self._track:
            self._track.solo = solo

    @property
    def is_visible(self):
        # type: () -> bool
        return self._track and self._track.is_visible

    @property
    def is_playing(self):
        # type: () -> bool
        return self.base_track.is_playing or any(
            sub_track.is_playing for sub_track in self.sub_tracks
        )

    @property
    def muted(self):
        # type: () -> bool
        return self._track and self._track.mute

    @muted.setter
    def muted(self, mute):
        # type: (bool) -> None
        if self._track:
            self._track.mute = mute

    @property
    def is_recording(self):
        # type: () -> bool
        return False

    @property
    def volume(self):
        # type: () -> float
        volume = self._track.mixer_device.volume.value if self._track else 0
        return volume_to_db(volume)

    @volume.setter
    def volume(self, volume):
        # type: (float) -> None
        volume = db_to_volume(volume)
        if self._track:
            Scheduler.defer(
                partial(
                    DeviceParameter.set_live_device_parameter,
                    self._track.mixer_device.volume,
                    volume,
                )
            )

    @property
    def has_audio_output(self):
        # type: () -> bool
        return self._track and self._track.has_audio_output

    # noinspection PyUnusedLocal
    def select(self):
        # type: () -> Optional[Sequence]
        if SongFacade.selected_track() == self:
            return None

        DomainEventBus.emit(AbstractTrackSelectedEvent(self._track))

        scrollable_tracks = list(SongFacade.scrollable_tracks())
        if len(scrollable_tracks) != 0 and self == scrollable_tracks[-1]:
            ApplicationViewFacade.focus_current_track()
        return Sequence().wait(2).done()

    def focus(self, show_browser=False):
        # type: (bool) -> Sequence
        # track can disappear out of view if this is done later
        self.color = TrackColorEnum.FOCUSED.int_value
        seq = Sequence()

        if show_browser and not ApplicationViewFacade.is_browser_visible():
            ApplicationViewFacade.show_browser()
            seq.defer()

            if SongFacade.selected_track() == self.base_track:
                seq.add(next(SongFacade.simple_tracks()).select)

        seq.add(self.select)
        return seq.done()

    def save(self):
        # type: () -> Sequence
        assert self.volume == 0

        track_color = self.color
        seq = Sequence()
        seq.add(partial(self.focus, show_browser=True))
        seq.add(Backend.client().save_track_to_sub_tracks)
        seq.wait_for_backend_event("track_focused")
        seq.add(partial(setattr, self, "color", track_color))
        seq.wait_for_backend_event("track_saved")

        return seq.done()

    def bars_left(self, scene_index):
        # type: (int) -> int
        """Returns the truncated number of bars left before the track stops on this particular scene"""
        clip = self.clip_slots[scene_index].clip
        if clip is not None and clip.is_playing:
            return clip.playing_position.bars_left
        else:
            return 0

    def fire(self, scene_index):
        # type: (int) -> None
        clip = self.clip_slots[scene_index].clip
        if clip is not None:
            clip.fire()

    def stop(self, scene_index=None, next_scene_index=None, immediate=False):
        # type: (Optional[int], Optional[int], bool) -> None
        """
        Will stop the track immediately or quantized
        the scene_index is useful for fine tuning the stop of abstract group tracks
        """
        if scene_index is None:
            self.base_track._track.stop_all_clips(not immediate)  # noqa
        else:
            clip = self.clip_slots[scene_index].clip
            if clip is not None and clip.is_playing:
                clip.stop(immediate=immediate)

    def scroll_volume(self, go_next):
        # type: (bool) -> None
        """Editing directly the mixer device volume"""
        volume = self._track.mixer_device.volume.value
        volume += 0.01 if go_next else -0.01
        volume = min(volume, 1)

        seq = Sequence()
        seq.defer()
        seq.add(
            partial(
                DeviceParameter.set_live_device_parameter,
                self._track.mixer_device.volume,
                volume,
            )
        )
        seq.add(lambda: StatusBar.show_message("Track volume: %.1f dB" % self.volume))
        seq.done()

    def get_all_simple_sub_tracks(self):
        # type: () -> List[SimpleTrack]
        sub_tracks = []
        for sub_track in self.sub_tracks:
            if sub_track.is_foldable:
                sub_tracks += sub_track.get_all_simple_sub_tracks()
            else:
                sub_tracks.append(sub_track)

        return sub_tracks  # noqa

    def add_or_replace_sub_track(self, sub_track, previous_sub_track=None):
        # type: (AbstractTrack, Optional[AbstractTrack]) -> None
        if sub_track in self.sub_tracks:
            return

        if previous_sub_track is None or previous_sub_track not in self.sub_tracks:
            self.sub_tracks.append(sub_track)
        else:
            sub_track_index = self.sub_tracks.index(previous_sub_track)
            self.sub_tracks[sub_track_index] = sub_track

    def get_automated_parameters(self, scene_index):
        # type: (int) -> Dict[DeviceParameter, SimpleTrack]
        """Due to AbstractGroupTrack we cannot do this only at clip level"""
        raise NotImplementedError

    def scroll_presets(self, go_next):
        # type: (bool) -> Sequence
        assert self.instrument, "track has not instrument"
        seq = Sequence()
        seq.add(self.arm_state.arm)
        seq.add(partial(self.instrument.preset_list.scroll, go_next))
        return seq.done()

    def disconnect(self):
        # type: () -> None
        super(AbstractTrack, self).disconnect()
        self.appearance.disconnect()

import time
from functools import partial

from typing import Optional

from protocol0.domain.lom.clip.ClipLoopChangedEvent import ClipLoopChangedEvent
from protocol0.domain.lom.track.group_track.external_synth_track.ExternalSynthTrack import (
    ExternalSynthTrack,
)
from protocol0.domain.lom.track.simple_track.SimpleDummyTrack import SimpleDummyTrack
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.domain.shared.scheduler.Scheduler import Scheduler
from protocol0.domain.shared.utils.timing import throttle
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.logging.Logger import Logger


class ExternalSynthTrackClipSynchronizerService(object):
    def __init__(self):
        # type: () -> None
        DomainEventBus.subscribe(ClipLoopChangedEvent, self._on_clip_loop_changed_event)
        self._midi_editing_until = None  # type: Optional[float]

    @throttle(duration=500)
    def _on_clip_loop_changed_event(self, event):
        # type: (ClipLoopChangedEvent) -> None
        """Synchronize loops"""
        current_track = SongFacade.current_track()
        if not isinstance(current_track, ExternalSynthTrack):
            return

        if isinstance(SongFacade.selected_track(), SimpleDummyTrack):
            return

        midi_clip = current_track.midi_track.clip_slots[SongFacade.selected_scene().index].clip

        # not a manual edition ..?
        if midi_clip is None or current_track.is_armed:
            return

        if event.live_clip != midi_clip._clip and (
            self._midi_editing_until is None or time.time() > self._midi_editing_until
        ):
            self._midi_editing_until = None
            Logger.warning("Please only edit the midi clip loop")
            return
        else:
            self._midi_editing_until = time.time() + 0.5

        audio_clip = current_track.audio_track.clip_slots[SongFacade.selected_scene().index].clip

        Scheduler.defer(partial(audio_clip.loop.match, midi_clip.loop))

        if current_track.audio_tail_track is None:
            return

        audio_tail_clip = current_track.audio_tail_track.clip_slots[
            SongFacade.selected_scene().index
        ].clip
        if audio_tail_clip is not None:
            Scheduler.defer(partial(audio_tail_clip.loop.match, midi_clip.loop))

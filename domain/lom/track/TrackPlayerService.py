from functools import partial

from typing import Optional

from protocol0.domain.lom.song.SongStoppedEvent import SongStoppedEvent
from protocol0.domain.lom.song.components.PlaybackComponent import PlaybackComponent
from protocol0.domain.lom.track.TrackRepository import TrackRepository
from protocol0.domain.lom.track.simple_track.SimpleTrack import SimpleTrack
from protocol0.domain.shared.errors.Protocol0Warning import Protocol0Warning
from protocol0.domain.shared.event.DomainEventBus import DomainEventBus
from protocol0.domain.shared.scheduler.Scheduler import Scheduler
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.logging.Logger import Logger
from protocol0.shared.sequence.Sequence import Sequence


class TrackPlayerService(object):
    """deprecated"""
    def __init__(self, playback_component, track_repository):
        # type: (PlaybackComponent, TrackRepository) -> None
        self._playback_component = playback_component
        self._track_repository = track_repository

    def toggle_track(self, track_name):
        # type: (str) -> None
        track = self._track_repository.find_simple_by_name(track_name)

        if len(track.clips) == 0:
            raise Protocol0Warning("%s has no clips" % track)

        self._toggle_track_first_clip(track)

    def _toggle_track_first_clip(self, track):
        # type: (SimpleTrack) -> Optional[Sequence]
        if len(track.clips) == 0:
            return None

        if track.is_playing:
            Logger.info("Stopping %s" % track)
            track.stop()
            return None

        Logger.info("Playing %s" % track)
        if not self._playback_component.is_playing:
            self._playback_component.stop_all_clips()

        seq = Sequence()
        clip = next((clip for clip in track.clips if not clip.muted), None)
        if not clip:
            clip = track.clips[0]
            clip.muted = False
            DomainEventBus.once(SongStoppedEvent, partial(setattr, clip, "muted", True))
            seq.defer()

        seq.add(clip.fire)
        return seq.done()

    def toggle_drums(self):
        # type: () -> None
        drum_tracks = SongFacade.drums_track().get_all_simple_sub_tracks()
        if any(track for track in drum_tracks if track.is_playing):
            for track in drum_tracks:
                track.stop(immediate=True)
        else:
            song_is_playing = SongFacade.is_playing()
            for track in drum_tracks:
                self._toggle_track_first_clip(track)

                # when the song is not playing clips are not starting at the same time
                if not song_is_playing:
                    self._playback_component.stop_playing()
                    Scheduler.defer(self._playback_component.start_playing)

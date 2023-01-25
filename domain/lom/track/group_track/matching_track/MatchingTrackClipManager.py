from functools import partial

from typing import Optional, List

from protocol0.domain.lom.clip.ClipInfo import ClipInfo
from protocol0.domain.lom.track.group_track.matching_track.MatchingTrackProxy import (
    MatchingTrackProxy,
)
from protocol0.domain.lom.track.simple_track.audio.SimpleAudioTrack import SimpleAudioTrack
from protocol0.domain.shared.backend.Backend import Backend
from protocol0.domain.shared.utils.list import find_if
from protocol0.shared.sequence.Sequence import Sequence


class MatchingTrackClipManager(object):
    def __init__(self, track_proxy):
        # type: (MatchingTrackProxy) -> None
        self._track_proxy = track_proxy
        from protocol0.domain.lom.track.simple_track.audio.SimpleAudioTrack import SimpleAudioTrack

        # merge the file path mapping into one reference
        if isinstance(self._track_proxy.base_track, SimpleAudioTrack):
            self._track_proxy.audio_track.audio_to_midi_clip_mapping.update(
                self._track_proxy.base_track.audio_to_midi_clip_mapping
            )
            self._track_proxy.base_track.audio_to_midi_clip_mapping = (
                self._track_proxy.audio_track.audio_to_midi_clip_mapping
            )

    def broadcast_clips(self, flattened_track, clip_infos):
        # type: (SimpleAudioTrack, List[ClipInfo]) -> Optional[Sequence]
        audio_track = self._track_proxy.audio_track

        seq = Sequence()

        for clip_info in clip_infos:
            seq.add(partial(self._broadcast_clip, clip_info, flattened_track))

        seq.add(
            lambda: Backend.client().show_success(
                "%s / %s clips replaced"
                % (sum(c.clips_replaced_count for c in clip_infos), len(audio_track.clips))
            )
        )

        return seq.done()

    def _broadcast_clip(self, clip_info, source_track):
        # type:  (ClipInfo, SimpleAudioTrack) -> Optional[Sequence]
        source_cs = source_track.clip_slots[clip_info.index]
        assert source_cs.clip is not None, "Couldn't find clip at index %s" % clip_info.index

        audio_track = self._track_proxy.audio_track
        matching_clip_slots = [
            cs for cs in audio_track.clip_slots if clip_info.matches_clip_slot(audio_track, cs)
        ]
        clip_info.clips_replaced_count = len(matching_clip_slots)

        # new clip
        if len(matching_clip_slots) == 0:
            dest_cs = self._track_proxy.audio_track.clip_slots[source_cs.index]
            if dest_cs.clip is not None:
                dest_cs = find_if(lambda c: c.clip is None, self._track_proxy.audio_track.clip_slots)  # type: ignore

            assert dest_cs is not None, "Expected empty clip slot for new clip"

            clip_info.clips_replaced_count = 1

            return source_cs.duplicate_clip_to(dest_cs)

        seq = Sequence()
        for dest_cs in matching_clip_slots:
            seq.add(partial(audio_track.replace_clip_sample, dest_cs, source_cs))

        seq.add(Backend.client().close_samples_windows)

        return seq.done()

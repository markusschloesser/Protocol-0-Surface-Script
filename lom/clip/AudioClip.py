from functools import partial
from math import floor

from typing import TYPE_CHECKING, Any

import Live
from protocol0.lom.clip.Clip import Clip
from protocol0.utils.decorators import p0_subject_slot

if TYPE_CHECKING:
    from protocol0.lom.track.simple_track.SimpleAudioTrack import SimpleAudioTrack
    from protocol0.lom.clip_slot.AudioClipSlot import AudioClipSlot


# noinspection PyPropertyAccess
class AudioClip(Clip):
    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(AudioClip, self).__init__(*a, **k)
        self.track = self.track  # type: SimpleAudioTrack
        self.clip_slot = self.clip_slot  # type: AudioClipSlot
        self._warping_listener.subject = self._clip

    @p0_subject_slot("warping")
    def _warping_listener(self):
        # type: () -> None
        if self.warping:
            self.parent.defer(partial(setattr, self, "looping", True))
        # noinspection PyUnresolvedReferences
        self.notify_length()

    @property
    def warping(self):
        # type: () -> float
        return self._clip.warping if self._clip else 0

    @warping.setter
    def warping(self, warping):
        # type: (float) -> None
        if self._clip:
            self._clip.warping = warping

    @property
    def warp_mode(self):
        # type: () -> Live.Clip.WarpMode
        return self._clip.warp_mode if self._clip else Live.Clip.WarpMode.beats

    @warp_mode.setter
    def warp_mode(self, warp_mode):
        # type: (Live.Clip.WarpMode) -> None
        if self._clip:
            self._clip.warp_mode = warp_mode

    @p0_subject_slot("looping")
    def _looping_listener(self):
        # type: () -> None
        if self.warping:
            # enforce looping
            self.parent.defer(partial(setattr, self._clip, "looping", True))

    @property
    def file_path(self):
        # type: () -> str
        return self._clip.file_path if self._clip else ""

    @property
    def tail_bar_length(self):
        # type: () -> int
        total_length = floor(self.end_marker - self.start_marker)
        beat_tail_length = total_length - self.length
        # this can happen if we manually increase the linked midi clip length
        if beat_tail_length < 0:
            return 0
        return int(beat_tail_length / self.song.signature_numerator)

    def post_record(self):
        # type: () -> None
        super(AudioClip, self).post_record()
        self.warp_mode = Live.Clip.WarpMode.complex

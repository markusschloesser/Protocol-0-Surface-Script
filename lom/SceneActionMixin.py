from functools import partial
from math import floor

from typing import TYPE_CHECKING, Optional, cast

from protocol0.components.SessionToArrangementManager import SessionToArrangementManager
from protocol0.lom.track.group_track.ExternalSynthTrack import ExternalSynthTrack
from protocol0.lom.track.simple_track.SimpleAudioTailTrack import SimpleAudioTailTrack
from protocol0.sequence.Sequence import Sequence
from protocol0.utils.utils import scroll_values

if TYPE_CHECKING:
    from protocol0.lom.Scene import Scene


# noinspection PyTypeHints
class SceneActionMixin(object):
    def check_scene_length(self):
        # type: (Scene) -> None
        self.parent.defer(self.scene_name.update)

    def on_beat_changed(self):
        # type: (Scene) -> None
        if self.is_recording:
            return
        # trigger on last beat
        if self.current_bar == self.bar_length - 1:
            if self.current_beat == self.song.signature_numerator - 1 or SessionToArrangementManager.IS_BOUNCING:
                self._fire_next_scene()

        if self.current_beat == 0 and not SessionToArrangementManager.IS_BOUNCING:
            self.parent.defer(self.scene_name.update)

    def _fire_next_scene(self):
        # type: (Scene) -> Optional[Sequence]
        if self.next_scene_fired:
            return None

        self.next_scene_fired = True

        self.parent.defer(self._play_audio_tails)

        next_scene = self.next_scene

        if self != next_scene:
            self.parent.defer(partial(next_scene._stop_previous_scene, self))

        seq = Sequence()
        if self == next_scene and SessionToArrangementManager.IS_BOUNCING:
            seq.add(self.song.stop_all_clips)
            seq.add(partial(self.parent.wait_bars, 2, self.song.stop_playing))
        else:
            seq.add(next_scene.fire)
        return seq.done()

    def select(self):
        # type: (Scene) -> None
        self.song.selected_scene = self

    def fire(self, stop_last=False, move_playing_position=False):
        # type: (Scene, bool, bool) -> Optional[Sequence]
        if not self._scene:
            return None

        self.next_scene_fired = False  # when looping the same (potentially last) scene

        if move_playing_position:
            self.parent.defer(partial(self.jump_to, self.selected_playing_position))

        seq = Sequence()

        # handles click sound when the previous scene plays shortly
        if stop_last and self.song.playing_scene and self.song.playing_scene != self:
            seq.add(wait=1)
            seq.add(partial(self._stop_previous_scene, self.song.playing_scene))

        seq.add(self._scene.fire)
        seq.add(complete_on=self.is_triggered_listener)

        return seq.done()

    def pre_fire(self):
        # type: (Scene) -> Sequence
        self.fire()
        self.song.stop_playing()
        from protocol0.lom.Scene import Scene

        Scene.PLAYING_SCENE = self
        seq = Sequence()
        seq.add(wait=2)
        return seq.done()

    def _stop_previous_scene(self, previous_playing_scene, immediate=False):
        # type: (Scene, Optional[Scene], bool) -> None
        if previous_playing_scene is None or previous_playing_scene == self:
            return

        # manually stopping previous scene because we don't display clip slot stop buttons
        for track in previous_playing_scene.tracks:
            if track in self.tracks or isinstance(track, SimpleAudioTailTrack):
                continue

            track.stop(immediate=immediate)

        if immediate:
            previous_playing_scene.scene_name.update(display_bar_count=False)

    def _play_audio_tails(self):
        # type: (Scene) -> None
        # playing tails
        for clip in self.audio_tail_clips:
            abstract_track = cast(ExternalSynthTrack, clip.track.abstract_track)
            # do not trigger tail on monophonic loop
            if abstract_track.instrument.MONOPHONIC and self.next_scene.clip_slots[clip.track.index].clip:
                continue
            else:
                clip.play_and_mute()

    def mute_audio_tails(self):
        # type: (Scene) -> None
        for clip in self.audio_tail_clips:
            clip.mute_if_scene_changed()

    def delete(self):
        # type: (Scene) -> Optional[Sequence]
        if self._scene and not self.deleted:  # type: ignore[has-type]
            self.deleted = True
            return self.song.delete_scene(self.index)
        return None

    def toggle_loop(self):
        # type: (Scene) -> None
        """ for a scene solo means looped """
        from protocol0.lom.Scene import Scene

        if self != self.song.looping_scene:  # solo activation
            previous_looping_scene = self.song.looping_scene
            Scene.LOOPING_SCENE = self
            if self != self.song.playing_scene:
                self.fire()
            if previous_looping_scene:
                previous_looping_scene.scene_name.update()
        else:  # solo inactivation
            Scene.LOOPING_SCENE = None

        self.scene_name.update()

    def split(self):
        # type: (Scene) -> Sequence
        bar_length = self.SELECTED_DUPLICATE_SCENE_BAR_LENGTH
        seq = Sequence()
        seq.add(partial(self.song.duplicate_scene, self.index))
        seq.add(lambda: self.song.selected_scene._crop_clips_to_bar_length(bar_length=-bar_length))
        seq.add(partial(self._crop_clips_to_bar_length, bar_length=bar_length))
        for track in self.song.external_synth_tracks:
            if track.audio_tail_track and track.audio_tail_track.clip_slots[self.index]:
                seq.add([track.audio_tail_track.clip_slots[self.index].clip.delete])
        return seq.done()

    def _crop_clips_to_bar_length(self, bar_length):
        # type: (Scene, int) -> None
        for clip in self.clips:
            if isinstance(clip.track, SimpleAudioTailTrack):
                continue

            if 0 < bar_length < clip.bar_length:
                clip.bar_length = min(clip.bar_length, bar_length)
            elif bar_length < 0 and clip.bar_length > abs(bar_length):
                offset = clip.length - abs(bar_length) * self.song.signature_numerator
                clip.start_marker += offset
                clip.loop_start += offset

    def scroll_position(self, go_next):
        # type: (Scene, bool) -> None
        playing_position = self.playing_position if self.has_playing_clips else self.selected_playing_position
        bar_position = playing_position / self.song.signature_numerator
        rounded_bar_position = floor(bar_position) if go_next else round(bar_position)
        next_bar_position = scroll_values(range(0, self.bar_length), rounded_bar_position, go_next=go_next)

        self.selected_playing_position = next_bar_position * self.song.signature_numerator

        if self.has_playing_clips:
            self.jump_to(self.selected_playing_position)

        self.scene_name.update(display_selected_bar_count=True)

    def jump_to(self, next_position):
        # type: (Scene, float) -> None
        playing_position = self.playing_position if self.has_playing_clips else self.selected_playing_position
        beat_offset = next_position - playing_position
        self.song.scrub_by(beat_offset)

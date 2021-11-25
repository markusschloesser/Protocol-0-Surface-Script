from protocol0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent


class SetFixerManager(AbstractControlSurfaceComponent):
    def fix(self):
        # type: () -> None
        """ Fix the current set to the current standard regarding naming / coloring etc .."""
        self.parent.logManager.clear()
        self._validate_tracks()
        self._validate_instruments()

        self._refresh_tracks_appearance()
        self._refresh_clips_appearance()
        self.refresh_scenes_appearance()

        self.parent.show_message("Set fixed")

    def _validate_tracks(self):
        # type: () -> None
        for abstract_track in self.song.abstract_tracks:
            self.parent.validatorManager.validate_object(abstract_track)
        for simple_track in self.song.simple_tracks:
            self.parent.validatorManager.validate_object(simple_track)

    def _validate_instruments(self):
        # type: () -> None
        for simple_track in self.song.simple_tracks:
            instrument = simple_track.instrument
            if instrument and not instrument.selected_preset and not simple_track.name == instrument.NAME:
                self.parent.log_error(
                    "Couldn't find the selected preset of %s (instrument %s)"
                    % (simple_track.abstract_track, instrument)
                )

    def _refresh_clips_appearance(self):
        # type: () -> None
        for clip in (clip for track in self.song.simple_tracks for clip in track.clips):
            clip.refresh_appearance()

    def _refresh_tracks_appearance(self):
        # type: () -> None
        for track in reversed(list(self.song.abstract_tracks)):
            track.refresh_appearance()

    def refresh_scenes_appearance(self):
        # type: () -> None
        for scene in self.song.scenes:
            scene.scene_name.update()

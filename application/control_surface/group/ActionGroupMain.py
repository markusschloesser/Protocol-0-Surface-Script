from functools import partial

from typing import Optional

from protocol0.application.control_surface.ActionGroupInterface import ActionGroupInterface
from protocol0.domain.lom.device.DeviceService import DeviceService
from protocol0.domain.lom.instrument.InstrumentDisplayService import InstrumentDisplayService
from protocol0.domain.lom.instrument.preset.InstrumentPresetScrollerService import (
    InstrumentPresetScrollerService,
)
from protocol0.domain.lom.set.MixingService import MixingService
from protocol0.domain.lom.song.components.TempoComponent import TempoComponent
from protocol0.domain.lom.track.TrackAutomationService import TrackAutomationService
from protocol0.domain.track_recorder.RecordTypeEnum import RecordTypeEnum
from protocol0.domain.track_recorder.TrackRecorderService import TrackRecorderService
from protocol0.shared.SongFacade import SongFacade
from protocol0.shared.sequence.Sequence import Sequence


# noinspection SpellCheckingInspection
class ActionGroupMain(ActionGroupInterface):
    """
    Main group: gathering most the functionalities. My faithful companion when producing on Live !
    """

    CHANNEL = 4

    def configure(self):
        # type: () -> None
        def record_track(record_type):
            # type: (RecordTypeEnum) -> Optional[Sequence]
            return self._container.get(TrackRecorderService).record_track(
                SongFacade.current_track(), record_type
            )

        # TAP tempo encoder
        self.add_encoder(
            identifier=1,
            name="tap tempo",
            on_press=self._container.get(TempoComponent).tap,
            on_scroll=self._container.get(TempoComponent).scroll,
        )

        # VELO encoder
        self.add_encoder(
            identifier=2,
            name="smooth selected clip velocities",
            on_scroll=lambda: SongFacade.selected_midi_clip().scale_velocities,
        )

        # AUTOmation encoder
        self.add_encoder(
            identifier=3,
            name="automation",
            on_press=lambda: self._container.get(TrackAutomationService).show_automation(go_next=True),
            on_long_press=lambda: self._container.get(
                TrackAutomationService
            ).select_or_sync_automation,
            on_scroll=lambda: partial(
                SongFacade.selected_clip().automation.scroll_envelopes,
                SongFacade.selected_track().devices.parameters,
            ),
        )

        # VOLume encoder
        self.add_encoder(
            identifier=4,
            name="volume",
            on_scroll=self._container.get(MixingService).scroll_all_tracks_volume,
        )

        # RECordAudio encoder
        self.add_encoder(
            identifier=5,
            name="record audio export",
            filter_active_tracks=True,
            on_press=lambda: partial(record_track, RecordTypeEnum.AUDIO_EXPORT),
            on_long_press=lambda: partial(record_track, RecordTypeEnum.AUDIO_EXPORT_ONE),
        )

        # RECordAudio 2 encoder
        self.add_encoder(
            identifier=6,
            name="record audio jam",
            filter_active_tracks=True,
            on_press=lambda: partial(record_track, RecordTypeEnum.AUDIO),
        )

        # MONitor encoder
        self.add_encoder(
            identifier=8,
            name="monitor",
            filter_active_tracks=True,
            on_press=lambda: SongFacade.current_track().monitoring_state.switch,
        )

        # RECord normal encoder
        self.add_encoder(
            identifier=9,
            name="record normal",
            filter_active_tracks=True,
            on_scroll=self._container.get(
                TrackRecorderService
            ).recording_bar_length_scroller.scroll,
            on_press=lambda: partial(record_track, RecordTypeEnum.MIDI),
            on_long_press=lambda: partial(record_track, RecordTypeEnum.MIDI_UNLIMITED),
        )

        # SELected parameter encoder
        self.add_encoder(
            identifier=13,
            name="selected parameter",
            on_scroll=self._container.get(DeviceService).scroll_selected_parameter,
        )

        # INSTrument encoder
        self.add_encoder(
            identifier=16,
            name="instrument",
            filter_active_tracks=True,
            on_press=lambda: partial(
                self._container.get(InstrumentDisplayService).show_instrument,
                SongFacade.current_track(),
            ),
            on_scroll=lambda: partial(
                self._container.get(InstrumentPresetScrollerService).scroll_presets_or_samples,
                SongFacade.current_track(),
            ),
        )

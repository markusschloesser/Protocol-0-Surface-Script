from typing import Any

from protocol0.enums.DeviceEnum import DeviceEnum
from protocol0.enums.InputRoutingTypeEnum import InputRoutingTypeEnum
from protocol0.lom.track.simple_track.SimpleInstrumentBusTrack import SimpleInstrumentBusTrack
from protocol0.validation.AbstractObjectValidator import AbstractObjectValidator
from protocol0.validation.sub_validators.AggregateValidator import AggregateValidator
from protocol0.validation.sub_validators.CallbackValidator import CallbackValidator
from protocol0.validation.sub_validators.PropertyValueValidator import PropertyValueValidator
from protocol0.validation.sub_validators.SimpleTrackHasDeviceValidator import SimpleTrackHasDeviceValidator


class SimpleInstrumentBusTrackValidator(AbstractObjectValidator, AggregateValidator):
    def __init__(self, track, *a, **k):
        # type: (SimpleInstrumentBusTrack, Any, Any) -> None
        validators = [
            PropertyValueValidator(track, "input_routing_type", InputRoutingTypeEnum.NO_INPUT),
            SimpleTrackHasDeviceValidator(track, DeviceEnum.DUMMY_RACK),
            CallbackValidator(track, lambda t: len(t.clips) == 1, None, "track should have one empty dummy clip"),
            CallbackValidator(track, lambda t: len(t.clips) == 1 and t.clips[0].muted, None,
                              "dummy clip should be muted"),
        ]
        self._validators = validators
        super(SimpleInstrumentBusTrackValidator, self).__init__(track, *a, **k)

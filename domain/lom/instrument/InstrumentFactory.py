from typing import Optional, List, Type

import protocol0.domain.lom.instrument.instrument as instrument_package
from protocol0.domain.lom.device.Device import Device
from protocol0.domain.lom.device.PluginDevice import PluginDevice
from protocol0.domain.lom.device.RackDevice import RackDevice
from protocol0.domain.lom.device.SimplerDevice import SimplerDevice
from protocol0.domain.lom.instrument.InstrumentInterface import InstrumentInterface
from protocol0.domain.shared.utils import import_package


class InstrumentFactory(object):
    _INSTRUMENT_CLASSES = []  # type: List[Type[InstrumentInterface]]

    @classmethod
    def get_instrument_class(cls, device):
        # type: (Device) -> Optional[Type[InstrumentInterface]]
        # checking for grouped devices
        if isinstance(device, RackDevice):
            device = cls._get_device_from_rack_device(device) or device

        if isinstance(device, PluginDevice):
            for _class in cls._get_instrument_classes():
                if _class.DEVICE_NAME.lower() == device.name.lower():
                    return _class
        elif isinstance(device, SimplerDevice):
            from protocol0.domain.lom.instrument.instrument.InstrumentSimpler import InstrumentSimpler

            return InstrumentSimpler
        elif device.can_have_drum_pads:
            from protocol0.domain.lom.instrument.instrument.InstrumentDrumRack import InstrumentDrumRack

            return InstrumentDrumRack

        return None

    @classmethod
    def _get_device_from_rack_device(cls, rack_device):
        # type: (RackDevice) -> Optional[Device]
        if len(rack_device.chains) and len(rack_device.chains[0].devices):
            # keeping only racks containing the same device
            device_types = list(set([type(chain.devices[0]) for chain in rack_device.chains if len(chain.devices)]))
            device_names = list(set([chain.devices[0].name for chain in rack_device.chains if len(chain.devices)]))
            if len(device_types) == 1 and len(device_names) == 1:
                return rack_device.chains[0].devices[0]

        return None

    @classmethod
    def _get_instrument_classes(cls):
        # type: () -> List[Type[InstrumentInterface]]
        if not cls._INSTRUMENT_CLASSES:
            import_package(instrument_package)
            cls._INSTRUMENT_CLASSES = InstrumentInterface.__subclasses__()

        return cls._INSTRUMENT_CLASSES

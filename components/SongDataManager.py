from functools import wraps
from pydoc import locate, classname

from typing import Any

from protocol0.AbstractControlSurfaceComponent import AbstractControlSurfaceComponent
from protocol0.enums.AbstractEnum import AbstractEnum
from protocol0.errors.Protocol0Error import Protocol0Error
from protocol0.errors.SongDataError import SongDataError
from protocol0.my_types import Func, T
from protocol0.utils.utils import class_attributes

SYNCHRONIZABLE_CLASSE_NAMES = set()


def song_synchronizable_class(cls):
    # type: (T) -> T
    SYNCHRONIZABLE_CLASSE_NAMES.add(classname(cls, ""))
    return cls


def save_song_data(func):
    # type: (Func) -> Func
    @wraps(func)
    def decorate(*a, **k):
        # type: (Any, Any) -> None
        func(*a, **k)
        from protocol0 import Protocol0
        Protocol0.SELF.songDataManager.store_class_data(a[0])

    return decorate


class SongDataManager(AbstractControlSurfaceComponent):
    DEBUG = True

    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(SongDataManager, self).__init__(*a, **k)
        self.restore_data()

    def save(self):
        # type: () -> None
        for cls_fqdn in SYNCHRONIZABLE_CLASSE_NAMES:
            cls = locate(cls_fqdn)
            self.store_class_data(cls)

    def store_class_data(self, cls):
        # type: (Any) -> None
        attributes = class_attributes(cls)
        self.song.set_data(classname(cls, ""), attributes)

    def restore_data(self):
        # type: () -> None
        try:
            self._restore_data()
        except SongDataError as e:
            self.parent.log_error(str(e))
            self.parent.log_notice("setting %s song data to {}")
            self.clear_data(save_set=False)
            self.parent.show_message("Inconsistent song data please save the set")

    def _restore_data(self):
        # type: () -> None
        if len(list(SYNCHRONIZABLE_CLASSE_NAMES)) == 0:
            self.parent.log_error("no song synchronizable class detected")
            return

        for cls_fqdn in SYNCHRONIZABLE_CLASSE_NAMES:
            cls = locate(cls_fqdn)
            if not cls:
                self.parent.log_error("Couldn't locate %s" % cls_fqdn)
                continue
            class_data = self.song.get_data(cls_fqdn, {})
            if self.DEBUG:
                self.parent.log_info("class_data of %s: %s" % (cls_fqdn, class_data))
            if not isinstance(class_data, dict):
                raise SongDataError("%s song data : expected dict, got %s" % (cls_fqdn, class_data))

            for key, value in class_data.items():
                if AbstractEnum.is_json_enum(value):
                    try:
                        value = AbstractEnum.from_json_dict(value)
                    except Protocol0Error as e:
                        raise SongDataError(e)
                if not hasattr(cls, key):
                    raise SongDataError("Invalid song data, attribute does not exist %s.%s" % (cls_fqdn, key))
                if isinstance(getattr(cls, key), AbstractEnum) and not isinstance(value, AbstractEnum):
                    raise SongDataError("inconsistent AbstractEnum value for %s.%s : got %s" % (cls_fqdn, key, value))
                setattr(cls, key, value)

    def clear_data(self, save_set=True):
        # type: (bool) -> None
        for cls_fqdn in SYNCHRONIZABLE_CLASSE_NAMES:
            self.parent.log_notice("Clearing song data of %s" % cls_fqdn)
            self.song.set_data(cls_fqdn, {})

        if save_set:
            self.system.save_set()

from p0_system_api.api.default_api import P0SystemAPI
from typing import TYPE_CHECKING, Any, Optional

from _Framework.ControlSurface import get_control_surfaces
from _Framework.SubjectSlot import SlotManager, Subject
from protocol0.utils.utils import find_if

if TYPE_CHECKING:
    from protocol0.lom.Song import Song
    from protocol0.Protocol0 import Protocol0


class AbstractObject(SlotManager, Subject):
    def __init__(self, *a, **k):
        # type: (Any, Any) -> None
        super(AbstractObject, self).__init__(*a, **k)
        from protocol0 import Protocol0

        if Protocol0.SELF:
            parent = Protocol0.SELF  # type: Optional[Protocol0]
        else:
            parent = find_if(lambda cs: isinstance(cs, Protocol0), get_control_surfaces())
        assert parent
        self._parent = parent  # type: Protocol0
        self.deleted = False

    def __repr__(self):
        # type: () -> str
        out = "P0 %s" % self.__class__.__name__
        if hasattr(self, "base_name") and self.base_name:
            out += ": %s" % self.base_name
        elif hasattr(self, "name"):
            out += ": %s" % self.name
        if hasattr(self, "index"):
            out += " (%s)" % (self.index + 1)
        if self.deleted:
            out += " - DELETED"

        return out

    def __ne__(self, obj):
        # type: (object) -> bool
        return not obj or not self == obj

    @property
    def system(self):
        # type: () -> P0SystemAPI
        return self.parent.p0_system_api_client

    @property
    def parent(self):
        # type: () -> Protocol0
        return self._parent

    @property
    def session_view_active(self):
        # type: () -> bool
        return self.parent.application().view.is_view_visible('Session')

    @property
    def arrangement_view_active(self):
        # type: () -> bool
        return not self.session_view_active

    @property
    def song(self):
        # type: () -> Optional[Song]
        return self.parent.protocol0_song

    def refresh_appearance(self):
        # type: () -> None
        pass

from dataclasses import dataclass


ACTION_NONE = "none"
ACTION_SEND_OPEN = "send_open"
ACTION_SEND_CLOSE = "send_close"


def _clamp_position(value):
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


@dataclass
class MovementModel:
    time_open: float
    time_close: float
    position: float = 0.0
    target_position: float = 0.0
    moving_open: bool = False
    moving_close: bool = False
    state: str = "open"
    last_time: float | None = None

    def __post_init__(self):
        if self.time_open <= 0 or self.time_close <= 0:
            raise ValueError("time_open and time_close must be > 0")
        self.position = _clamp_position(self.position)
        self.target_position = _clamp_position(self.target_position)
        self._sync_terminal_state()

    @property
    def velocity_open(self):
        return 1.0 / self.time_open

    @property
    def velocity_close(self):
        return 1.0 / self.time_close

    def current_position_percent(self):
        return int(round(self.position * 100.0))

    def set_position_percent(self, percent):
        self.position = _clamp_position(float(percent) / 100.0)
        self.target_position = self.position
        self.moving_open = False
        self.moving_close = False
        self._sync_terminal_state()

    def command_open(self, now, target_position=0.0):
        self.last_time = now
        self.target_position = _clamp_position(target_position)
        self.moving_open = True
        self.moving_close = False
        self.state = "opening"
        return ACTION_SEND_OPEN

    def command_close(self, now, target_position=1.0):
        self.last_time = now
        self.target_position = _clamp_position(target_position)
        self.moving_open = False
        self.moving_close = True
        self.state = "closing"
        return ACTION_SEND_CLOSE

    def command_to_position(self, now, target_position):
        target = _clamp_position(target_position)
        self.target_position = target
        if target > self.position:
            return self.command_close(now, target_position=target)
        if target < self.position:
            return self.command_open(now, target_position=target)
        return ACTION_NONE

    def stop(self):
        if self.moving_open:
            self.moving_open = False
            self.state = "stopped"
            self._sync_terminal_state()
            return ACTION_SEND_CLOSE
        if self.moving_close:
            self.moving_close = False
            self.state = "stopped"
            self._sync_terminal_state()
            return ACTION_SEND_OPEN
        self._sync_terminal_state()
        return ACTION_NONE

    def tick(self, now):
        if self.last_time is None:
            self.last_time = now
            return ACTION_NONE

        dt = max(0.0, now - self.last_time)
        self.last_time = now
        if not self.moving_open and not self.moving_close:
            self._sync_terminal_state()
            return ACTION_NONE

        if self.moving_close:
            self.position = _clamp_position(self.position + dt * self.velocity_close)
            if self.position >= self.target_position:
                self.position = self.target_position
                self.moving_close = False
                if self.target_position < 1.0:
                    self.state = "stopped"
                    self._sync_terminal_state()
                    return ACTION_SEND_OPEN
                self.state = "closed"
                return ACTION_NONE
            self.state = "closing"
            return ACTION_NONE

        if self.moving_open:
            self.position = _clamp_position(self.position - dt * self.velocity_open)
            if self.position <= self.target_position:
                self.position = self.target_position
                self.moving_open = False
                if self.target_position > 0.0:
                    self.state = "stopped"
                    self._sync_terminal_state()
                    return ACTION_SEND_CLOSE
                self.state = "open"
                return ACTION_NONE
            self.state = "opening"
            return ACTION_NONE

        return ACTION_NONE

    def _sync_terminal_state(self):
        if self.position <= 0.0:
            self.position = 0.0
            if not self.moving_open and not self.moving_close:
                self.state = "open"
        elif self.position >= 1.0:
            self.position = 1.0
            if not self.moving_open and not self.moving_close:
                self.state = "closed"

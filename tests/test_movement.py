import unittest

from custom_components.schanz_rolladen.movement import (
    ACTION_NONE,
    ACTION_SEND_CLOSE,
    ACTION_SEND_OPEN,
    MovementModel,
)


class MovementModelTests(unittest.TestCase):
    def test_close_to_midpoint_requests_stop_signal(self):
        model = MovementModel(time_open=50.0, time_close=50.0)
        model.position = 0.0
        action = model.command_close(now=0.0, target_position=0.5)
        self.assertEqual(action, ACTION_SEND_CLOSE)

        action = model.tick(now=25.0)
        self.assertEqual(model.current_position_percent(), 50)
        self.assertEqual(action, ACTION_SEND_OPEN)
        self.assertFalse(model.moving_close)

    def test_open_to_midpoint_requests_stop_signal(self):
        model = MovementModel(time_open=50.0, time_close=50.0)
        model.position = 1.0
        action = model.command_open(now=0.0, target_position=0.25)
        self.assertEqual(action, ACTION_SEND_OPEN)

        action = model.tick(now=40.0)
        self.assertEqual(model.current_position_percent(), 25)
        self.assertEqual(action, ACTION_SEND_CLOSE)
        self.assertFalse(model.moving_open)

    def test_stop_from_closing_sends_open(self):
        model = MovementModel(time_open=50.0, time_close=50.0)
        model.command_close(now=1.0)
        action = model.stop()
        self.assertEqual(action, ACTION_SEND_OPEN)

    def test_no_action_when_target_is_current_position(self):
        model = MovementModel(time_open=50.0, time_close=50.0)
        model.position = 0.4
        action = model.command_to_position(now=2.0, target_position=0.4)
        self.assertEqual(action, ACTION_NONE)


if __name__ == "__main__":
    unittest.main()


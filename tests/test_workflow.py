"""Offline regressions: no credentials, browser, or course submissions required."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

ROOT = Path(__file__).absolute().parents[1]


def load_module(name):
    api = types.ModuleType("api")
    api.cfg = {"courseOfferingId": "off", "sectionId": "section",
               "activities": [{"id": "a"}, {"id": "b"}]}
    api.refresh = Mock()
    util = types.ModuleType("util")
    util.post, util.get, util.upload = Mock(), Mock(), Mock(return_value="blob")
    tts = types.ModuleType("tts")
    tts.speak = Mock()
    answers = types.ModuleType("answers")
    answers.shot_answer = Mock(return_value="Hello.")
    spec = importlib.util.spec_from_file_location("test_target_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"api": api, "util": util, "tts": tts, "answers": answers}):
        spec.loader.exec_module(module)
    module.time = Mock()
    return module


class CourseProgressTests(unittest.TestCase):
    def test_course_status_overrides_stale_attempts_in_both_directions(self):
        module = load_module("tasks")
        module.post.side_effect = [
            (200, [{"activityId": "a", "status": "COMPLETED", "attemptId": "old"},
                   {"activityId": "b", "status": "IN_PROGRESS", "attemptId": "current"}]),
            (200, [{"activityId": "a", "status": "NOT_DONE", "taskId": ""},
                   {"activityId": "b", "status": "COMPLETED", "taskId": "new"}]),
        ]
        progress = module.progress_map()
        self.assertEqual(progress["a"]["status"], "NOT_DONE")
        self.assertEqual(progress["b"]["status"], "COMPLETED")
        # taskId 与作答上下文不同源：只能单独保留，不能覆盖 attemptId
        self.assertEqual(progress["b"]["attemptId"], "current")
        self.assertEqual(progress["b"]["taskId"], "new")
        module.post.assert_called_with("learning-content/progress/my/off/section", {"activityIds": ["a", "b"]})

    def test_failed_or_empty_course_progress_does_not_fall_back_to_stale_state(self):
        for result in ((503, {}), (200, {}), (200, [])):
            with self.subTest(result=result):
                module = load_module("tasks")
                module.post.side_effect = [
                    (200, [{"activityId": "a", "status": "COMPLETED", "attemptId": "old"}]), result]
                with self.assertRaises(RuntimeError):
                    module.progress_map()

    def test_missing_activity_is_warned_and_treated_as_not_done(self):
        module = load_module("tasks")
        module.post.side_effect = [
            (200, [{"activityId": "a", "status": "COMPLETED", "attemptId": "old"}]),
            (200, [{"activityId": "a", "status": "COMPLETED", "taskId": ""}]),
        ]
        with patch("builtins.print") as out:
            progress = module.progress_map()
        self.assertNotIn("b", progress)  # 缺条目 = 未完成，交给 run.py 继续处理
        self.assertEqual(progress["a"]["attemptId"], "old")
        self.assertIn("b", " ".join(str(c.args[0]) for c in out.call_args_list))


class SituationalTests(unittest.TestCase):
    def setup_scene(self, training_mode="Exam"):
        module = load_module("sit_task")
        module.post.side_effect = [(200, {"attemptId": "attempt"}),
                                   (200, {"sceneId": "scene", "activityExecutionId": "execution"}),
                                   (200, {})]
        module.get.side_effect = [(200, {"trainingMode": training_mode}), (200, {"isEnding": True})]
        return module

    def assert_not_completed(self, module):
        self.assertFalse(any(call.args[0].endswith("/complete") for call in module.post.call_args_list))

    def test_creates_attempt_before_scene_and_uses_preview_training_mode(self):
        for mode in ("Practice", "Exam"):
            with self.subTest(mode=mode):
                module = self.setup_scene(mode)
                self.assertIn("complete=200", module.do_situational({"id": "activity"}))
                self.assertEqual(module.post.call_args_list[0].args[0],
                                 "learning-practice/attempts/off/activity/%s/situational" % mode.lower())
                self.assertEqual(module.post.call_args_list[1].args[0],
                                 "learning-practice/contents/situational/activity/scene")
                self.assertEqual(module.post.call_args_list[-1].args[1], {"trainingType": mode})

    def test_explicit_mode_override_is_preserved(self):
        module = self.setup_scene("Exam")
        module.do_situational({"id": "activity"}, mode="practice")
        self.assertEqual(module.post.call_args_list[-1].args[1], {"trainingType": "Practice"})

    def test_invalid_training_mode_does_not_create_attempt(self):
        module = self.setup_scene("Unknown")
        self.assertIn("invalid-training-mode", module.do_situational({"id": "activity"}))
        module.post.assert_not_called()

    def test_stuck_scene_and_shot_limit_do_not_submit_completion(self):
        for limit in (2, 8):
            with self.subTest(limit=limit):
                module = self.setup_scene()
                module.get.side_effect = [(200, {"trainingMode": "Practice"})] + [
                    (200, {"shotId": "same", "timeLimit": 0})] * 8
                self.assertIn("scene-not-ended", module.do_situational({"id": "activity"}, max_shots=limit))
                self.assert_not_completed(module)

    def test_405_and_json_errors_do_not_refresh_or_complete(self):
        for error in ((405, ""), (403, {"error": "forbidden"}), (200, {})):
            with self.subTest(error=error):
                module = self.setup_scene()
                module.get.side_effect = [(200, {"trainingMode": "Practice"}), error]
                module.do_situational({"id": "activity"})
                module.api.refresh.assert_not_called()
                self.assert_not_completed(module)

    def test_failed_or_timed_out_review_does_not_advance_or_complete(self):
        for status in ("Failed", "Running"):
            with self.subTest(status=status):
                module = self.setup_scene()
                module.post.side_effect = [(200, {"attemptId": "attempt"}),
                                           (200, {"sceneId": "scene", "activityExecutionId": "execution"}),
                                           (200, {"executionId": "review"})]
                module.get.side_effect = [(200, {"trainingMode": "Exam"}),
                                          (200, {"shotId": "shot", "recordId": "record", "timeLimit": 30})] + [
                                              (200, {"status": status})] * 40
                with patch("builtins.open", mock_open(read_data=b"audio")):
                    result = module.do_situational({"id": "activity"})
                self.assertIn("review-", result)
                self.assert_not_completed(module)
                self.assertEqual(sum("next-shot" in call.args[0] for call in module.get.call_args_list), 1)

    def test_completion_http_error_is_reported(self):
        module = self.setup_scene()
        module.post.side_effect = [(200, {"attemptId": "attempt"}),
                                   (200, {"sceneId": "scene", "activityExecutionId": "execution"}), (500, {})]
        result = module.do_situational({"id": "activity"})
        self.assertTrue(result.startswith("complete-failed 500"), result)
        self.assertIn("attempt=attempt", result)
        self.assertIn("scene=execution", result)


if __name__ == "__main__":
    unittest.main()

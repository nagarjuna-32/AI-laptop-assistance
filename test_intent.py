import unittest
from intent import clean_text, detectIntent
import db

class TestIntentClassification(unittest.TestCase):
    def setUp(self):
        # Initialize database
        db.init_db()

    def test_clean_text_normalizations(self):
        self.assertEqual(clean_text("please open whats app"), "open whatsapp")
        self.assertEqual(clean_text("hey chinni open u tube"), "open youtube")
        self.assertEqual(clean_text("turn on blue tooth"), "turn on bluetooth")
        self.assertEqual(clean_text("play spotty fire"), "play spotify")
        self.assertEqual(clean_text("please open not pad"), "open notepad")
        self.assertEqual(clean_text("can you open calcy"), "open calculator")
        self.assertEqual(clean_text("activate coding mode"), "activate coding mood")

    def test_open_app_intent(self):
        res = detectIntent("open YouTube")
        self.assertEqual(res["intent"], "OPEN_APP")
        self.assertEqual(res["command"], "open")
        self.assertEqual(res["target"], "YouTube")
        self.assertEqual(res["needsConfirmation"], False)

    def test_risky_file_action(self):
        # Deleting files is dangerous -> needs confirmation
        res = detectIntent("delete file important.txt")
        self.assertEqual(res["intent"], "FILE_ACTION")
        self.assertEqual(res["command"], "delete")
        self.assertEqual(res["needsConfirmation"], True)

    def test_safe_volume_setting(self):
        # Changing volume is safe -> no confirmation
        res = detectIntent("volume up")
        self.assertEqual(res["intent"], "SYSTEM_SETTING")
        self.assertEqual(res["target"], "Volume")
        self.assertEqual(res["needsConfirmation"], False)

    def test_ask_ai_intent(self):
        res = detectIntent("what is DevOps")
        self.assertEqual(res["intent"], "ASK_AI")
        self.assertEqual(res["command"], "answer_question")
        self.assertEqual(res["target"], "what is DevOps")
        self.assertEqual(res["needsConfirmation"], False)

    def test_ambiguous_intent(self):
        res = detectIntent("open chrome music")
        self.assertEqual(res["intent"], "UNKNOWN")
        self.assertEqual(res["command"], "clarify")
        self.assertTrue(res["confidence"] < 80)
        self.assertEqual(res["needsConfirmation"], True)

    def test_custom_command_exact_study_mode(self):
        res = detectIntent("study mode")
        self.assertEqual(res["intent"], "CUSTOM_COMMAND")
        self.assertEqual(res["target"], "study mode")
        self.assertEqual(res["needsConfirmation"], False)

    def test_custom_command_similar_study_mode(self):
        res = detectIntent("start study mode")
        self.assertEqual(res["intent"], "CUSTOM_COMMAND")
        self.assertEqual(res["target"], "study mode")
        
        res_act = detectIntent("activate study mode")
        self.assertEqual(res_act["intent"], "CUSTOM_COMMAND")
        self.assertEqual(res_act["target"], "study mode")

    def test_custom_command_exact_coding_mood(self):
        res = detectIntent("coding mood")
        self.assertEqual(res["intent"], "CUSTOM_COMMAND")
        self.assertEqual(res["target"], "coding mood")

    def test_custom_command_similar_coding_mode(self):
        res = detectIntent("activate coding mode")
        self.assertEqual(res["intent"], "CUSTOM_COMMAND")
        self.assertEqual(res["target"], "coding mood")

    def test_unclear_speech(self):
        res = detectIntent("asdfghjkl")
        self.assertEqual(res["intent"], "UNKNOWN")
        self.assertTrue(res["confidence"] < 80)
        self.assertEqual(res["needsConfirmation"], True)
        self.assertEqual(res["clarification"], "I didn't catch that clearly. Please repeat.")

    def test_close_app_correct_routing(self):
        res = detectIntent("close the calculator")
        self.assertEqual(res["intent"], "CLOSE_APP")
        self.assertEqual(res["command"], "close")
        self.assertEqual(res["target"], "calculator")

    def test_time_now_system_info(self):
        res = detectIntent("what is the time now")
        self.assertEqual(res["intent"], "SYSTEM_INFO")
        self.assertEqual(res["command"], "time")

    def test_date_now_system_info(self):
        res = detectIntent("what is today's date")
        self.assertEqual(res["intent"], "SYSTEM_INFO")
        self.assertEqual(res["command"], "date")

    def test_close_study_mode(self):
        res = detectIntent("close the study mode")
        self.assertEqual(res["intent"], "CLOSE_APP")
        self.assertEqual(res["command"], "close_mode")
        self.assertEqual(res["target"], "study mode")

    def test_close_coding_mode(self):
        res = detectIntent("close the coding mode")
        self.assertEqual(res["intent"], "CLOSE_APP")
        self.assertEqual(res["command"], "close_mode")
        self.assertEqual(res["target"], "coding mood")

if __name__ == "__main__":
    unittest.main()


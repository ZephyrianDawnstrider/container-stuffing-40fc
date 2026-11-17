import unittest
from streamlit.testing.v1 import AppTest
class AppTests(unittest.TestCase):
    def test_demo_switch_and_repeat(self):
        at=AppTest.from_file('../app.py',default_timeout=30).run()
        self.assertFalse(at.exception)
        at.button[0].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.success),1)
        at.selectbox[0].select_index(2).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.success),0)
        at.button[0].click().run()
        self.assertEqual(len(at.success),1)
        other=AppTest.from_file('../app.py',default_timeout=30).run()
        self.assertEqual(other.selectbox[0].value['id'],'20dc')
        self.assertEqual(len(other.success),0)
    def test_no_jobs_no_button(self):
        at=AppTest.from_file('../app.py').run()
        at.checkbox[0].uncheck().run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.button),0)

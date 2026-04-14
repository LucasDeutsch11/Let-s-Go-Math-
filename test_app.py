import unittest
from app import app

class LetsGoMathTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Let's Go Math", response.data)

    def test_topics_page(self):
        response = self.app.get('/topics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Topics", response.data)

    def test_dashboard_redirect_if_not_logged_in(self):
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(b"Sign In", response.data)

    def test_start_practice(self):
        response = self.app.get('/start?difficulty=easy', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Practice Problem", response.data)

    def test_leaderboard_page(self):
        response = self.app.get('/leaderboard')
        self.assertIn(response.status_code, [200, 302])  # 302 if login required

if __name__ == '__main__':
    unittest.main()

import unittest

from APIv2.modules.ApplicationModel import (
    UserProfile,
    FacebookUserIdentifyExeception,
)
from TestBase import TestBase


class UserProfileTest(TestBase):

    def test_init(self):
        user_profile = UserProfile(username="testuser", facebookId=123456789)
        self.assertEqual(user_profile.username, "testuser")
        self.assertEqual(user_profile.facebookId, 123456789)

    def test_invalid_facebook_accessToken(self):
        expectedExeception = 'Error performing facebook user identification'
        with self.assertRaises(FacebookUserIdentifyExeception) as ve:
            UserProfile.fromFacebookAccessToken("1234", self.session)
        self.assertEqual(str(ve.exception), expectedExeception)


if __name__ == '__main__':
    unittest.main()

import unittest
import datetime
from APIv2.modules.ApplicationModel import (
    UserProfile,
    UserProfileSession,
    FacebookUserIdentifyExeception,
    TableBase
)
from TestBase import TestBase


class UserProfileTest(TestBase):

    def test_init(self):
        userProfile = UserProfile(username="testuser", facebookId=123456789)
        self.assertEqual(userProfile.username, "testuser")
        self.assertEqual(userProfile.facebookId, 123456789)

    def test_invalid_facebook_accessToken(self):
        expectedExeception = 'Error performing facebook user identification'
        with self.assertRaises(FacebookUserIdentifyExeception) as ve:
            UserProfile.fromFacebookAccessToken("1234", self.session)
        self.assertEqual(str(ve.exception), expectedExeception)


class UserProfileSessionTest(TestBase):

    def test_init(self):
        currentTime = datetime.datetime.now()
        userProfile = UserProfile(username="testuser", facebookId=123456789)
        userSession = UserProfileSession(
            profile=userProfile,
            sessionToken="1234token",
            expire=currentTime
        )
        self.assertEqual(userSession.profile, userProfile)
        self.assertEqual(userSession.sessionToken, "1234token")
        self.assertEqual(userSession.expire, currentTime)

    def test_create(self):
        TableBase.metadata.create_all(self.engine)
        currentTime = datetime.datetime.now()
        userProfile = UserProfile(username="testuser", facebookId=123456789)
        userSession = UserProfileSession.create(
            userProfile=userProfile,
            expire=currentTime,
            dbSession=self.session
        )
        self.assertEqual(userSession.profile, userProfile)
        self.assertGreater(len(userSession.sessionToken), 5)
        self.assertEqual(userSession.expire, currentTime)

        retrivedUserSession = self.session.query(
            UserProfileSession
        ).where(
            UserProfileSession.profile_id == userProfile.id
        ).first()

        self.assertEqual(retrivedUserSession.sessionToken, userSession.sessionToken)  # type: ignore
        self.assertEqual(retrivedUserSession.profile, userProfile)  # type: ignore
        self.assertEqual(retrivedUserSession.expire, currentTime)  # type: ignore

    def test_get(self):
        TableBase.metadata.create_all(self.engine)
        currentTime = datetime.datetime.now()
        expireTime = currentTime + datetime.timedelta(days=2)
        userProfile = UserProfile(username="testuser", facebookId=123456789)
        userSession = UserProfileSession.create(
            userProfile=userProfile,
            expire=expireTime,
            dbSession=self.session
        )

        userProfileRetrived = UserProfileSession.get(
            sessionToken=userSession.sessionToken,
            currentTime=currentTime,
            dbSession=self.session
        )

        self.assertEqual(userProfileRetrived, userProfile)

    def test_get_not_exist(self):
        TableBase.metadata.create_all(self.engine)
        currentTime = datetime.datetime.now()
        userProfileRetrived = UserProfileSession.get(
            sessionToken="nope",
            currentTime=currentTime,
            dbSession=self.session
        )
        self.assertEqual(userProfileRetrived, None)

    def test_expired(self):
        TableBase.metadata.create_all(self.engine)
        currentTime = datetime.datetime.now()
        expireTime = currentTime + datetime.timedelta(days=2)
        pastExpireTime = currentTime + datetime.timedelta(days=3)
        userProfile = UserProfile(username="testuser", facebookId=123456789)
        userSession = UserProfileSession.create(
            userProfile=userProfile,
            expire=expireTime,
            dbSession=self.session
        )

        retrivedUserSessionCount = self.session.query(
            UserProfileSession
        ).where(
            UserProfileSession.profile_id == userProfile.id
        ).count()
        self.assertEqual(retrivedUserSessionCount, 1)

        userProfileRetrived = UserProfileSession.get(
            sessionToken=userSession.sessionToken,
            currentTime=pastExpireTime,
            dbSession=self.session
        )
        self.assertEqual(userProfileRetrived, None)

        retrivedUserSessionCount = self.session.query(
            UserProfileSession
        ).where(
            UserProfileSession.profile_id == userProfile.id
        ).count()
        self.assertEqual(retrivedUserSessionCount, 0)


if __name__ == '__main__':
    unittest.main()

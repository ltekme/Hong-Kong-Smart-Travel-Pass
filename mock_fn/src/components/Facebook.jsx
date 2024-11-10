import { useEffect, useState } from "react";


export const fbAppId = "1592228174832411";

export const initFacebookSdk = async () => {
    await window.FB.init({
        appId: fbAppId,
        status: true,
        xfbml: true,
        version: 'v2.7' // or v2.7, v2.6, v2.5, v2.4, v2.3
    });
};

export const getFacebookAccessToken = async () => {
    // try get current session
    const loginStatus = await new Promise((resolve, reject) => {
        window.FB.getLoginStatus((response) => {
            if (response.status === 'not_authorized') {
                reject("User cancelled login or did not fully authorize.");
                return;
            }
            if (response.status !== 'connected') {
                resolve(null);
                return;
            }
            // check for expired access_token
            let currrentEpoch = Math.floor(new Date().getTime() / 1000);
            let expireEpoch = response.authResponse.data_access_expiration_time;
            if (expireEpoch <= currrentEpoch) {
                console.debug("Access token expired, need to re-auth")
                resolve(null);
                return
            }
            console.debug("Current session:", response.status, "\nAuth Token expire epoch:", expireEpoch, "\nCurrent Epoch:", currrentEpoch);
            resolve(response.authResponse);
            return;
        });
    });

    if (loginStatus) {
        return loginStatus.accessToken;
    }

    // Not logged in, show auth page
    return new Promise(async (resolve, reject) => {
        window.FB.login(function (response) {
            // if (responseresponse.authResponse)
            if (response.authResponse === null) {
                reject("User cancelled login or did not fully authorize.");
                return;
            }
            resolve(response.authResponse.accessToken);
            return;
        });
    });
};

export const getFacebookProfile = async (accessToken) => {
    return new Promise(async (resolve, reject) => {
        window.FB.api('/me', {
            access_token: accessToken,
            fields: 'id,name,picture'
        }, (response) => {
            if (!response || response.error) {
                reject(response.error.message);
                return;
            }
            resolve(response);
            return;
        });
    });
};

export const logoutFacebook = async () => {
    return new Promise((resolve, reject) => {
        window.FB.logout((response) => {
            resolve(response);
            return;
        });
    })
}

export const FacebookLogin = ({
    setUsernameCallback = () => { },
}) => {
    // const [profile, setProfile] = useState(null);
    const [connected, setConnected] = useState(false);
    const [accessToken, setAccessToken] = useState(null);
    const [error, setError] = useState(null);
    const [username, setUsername] = useState(null);
    const [userId, setUserId] = useState(null);
    const [userIcon, setUserIcon] = useState(null);

    useEffect(() => {
        initFacebookSdk();
    }, []);

    useEffect(() => {
        const grepInfo = async () => {
            const profile = await getFacebookProfile(accessToken);
            console.log(`User profile connected. \nCurrent profile: ${profile.id}(${profile.name})`);
            setUsername(profile.name);
            setUsernameCallback(profile.name);
            setUserId(profile.id);
            setUserIcon(profile.picture.data.url);
            setConnected(true);
            setError(null);
        };
        if (accessToken !== null) {
            grepInfo();
        }
    }, [accessToken]);

    const handleFacebookLogin = async () => {
        try {
            let accessToken = await getFacebookAccessToken();
            setAccessToken(accessToken);
        } catch (error) {
            setError(error);
            setConnected(false);
            console.error("Error logging in with Facebook: ", error);
        }
    };

    const handleLogout = async () => {
        await logoutFacebook();
        setConnected(false);
        setAccessToken(null);
        setUsername(null);
        setUserId(null);
        setUserIcon(null);
    }

    const handleGetProfile = async () => {
    }

    return (
        <div>
            <h2>Facebook Connect</h2>
            {error && <div style={{ color: "red" }}>{error.toString()}</div>}
            {
                !connected ? <button onClick={handleFacebookLogin}>Login with Facebook</button>
                    : <div>
                        <img src={userIcon} alt="User Icon" style={{ maxWidth: "50px" }} />{username}
                        <br />
                        User ID: {userId}
                        <br />
                        <button onClick={handleLogout}>Logout</button>
                        <button onClick={async () => {
                            let accessToken = await getFacebookAccessToken();
                            navigator.clipboard.writeText(accessToken);
                        }}>copy access token</button>
                        {/* <button onClick={handleGetSession}>Get Session</button> */}
                        <button onClick={handleGetProfile}>Create Profile(Server side)</button>
                    </div>
            }
        </div>
    );
};
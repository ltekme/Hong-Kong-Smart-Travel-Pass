import { useState, useEffect } from "react";
import "./css/style.css";
import "./css/font-awesome.min.css";
import { facebookAppId, defaultApiUrl } from "../Config";
import Swal from "sweetalert2";

export interface IFacebookProfile {
    id: string;
    name: string;
    gender: string;
    accessToken: string;
    profilePicture?: string;
    sessionExpire?: number;
    sessionId?: string;
}

export interface IHello {
    confirmAgree: boolean;
    setFacebookProfile: (profile: IFacebookProfile) => void;
}
export const Hello = ({
    confirmAgree,
    setFacebookProfile,
}: IHello) => { // outside for set here
    const [showLogin, setShowLogin] = useState(true);
    const [showImage, setShowImage] = useState(window.innerWidth >= 400);

    const [facebookInited, setFacebookInited] = useState(false);

    // const showImage = window.innerWidth >= 400;
    useEffect(() => {
        const handleResize = () => {
            setShowImage(window.innerWidth >= 450);
        };

        window.addEventListener('resize', handleResize);
        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    useEffect(() => {
        (function (d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) { return; }
            js = d.createElement(s) as HTMLScriptElement;
            js.id = id;
            js.src = "https://connect.facebook.net/en_US/sdk.js";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));


        window.fbAsyncInit = function () {
            window.FB.init({
                appId: facebookAppId,
                xfbml: true,
                version: 'v21.0' // the-graph-api-version-for-your-app
            });
        };
        setFacebookInited(true);
    }, []);

    const handleFBLogin = () => {
        console.log('Click FB Login');

        if (!facebookInited) {
            return
        }

        try {
            const processProfileData = async (profileDetails: any, loginResponse: any) => {
                try {
                    const data = profileDetails.picture.data.url;  // https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=523024447160668&height=50&width=50&ext=1733251735&hash=AbZ3mHor3ZeZmBCb4eFd3qC2
                    const profileBase64 = await convertToBase64(data);
                    console.log(`Got faceboot response ${JSON.stringify(profileDetails, null, 4)} for ${profileDetails.name}`);

                    const sessionData = await fetch(`${defaultApiUrl}/get_session`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            'accessToken': loginResponse.authResponse.accessToken
                        })
                    })
                    if (!sessionData.ok) {
                        throw `Error cannot process profile\n ${JSON.stringify(sessionData.json())}`
                    }

                    const jsonSessionData = await sessionData.json();


                    setFacebookProfile({
                        accessToken: loginResponse.authResponse.accessToken,
                        profilePicture: profileBase64,
                        id: profileDetails.id,
                        name: profileDetails.name,
                        gender: profileDetails.gender,
                        sessionId: jsonSessionData.sessionId,
                        sessionExpire: jsonSessionData.expire,
                    });
                } catch (e) {
                    console.error(`Error processing user profile\n${e}`)
                    Swal.fire({
                        title: "Error processing your profile",
                        text: "See console for details",
                        icon: "error"
                    });
                }
                setShowLogin(false);
            };

            window.FB.login(function (loginResponse) {
                if (loginResponse.authResponse) {
                    console.log('Welcome!  Fetching your information.... ');
                    window.FB.api('/me', {
                        fields: 'id, name, picture, gender' //me?fields=posts{full_picture,message} 能拿到post中圖片
                    }, e => { processProfileData(e, loginResponse) });
                }
            });
        } catch (e) {
            console.error(e);
            setShowLogin(false);
            Swal.fire({
                title: "Facebook login failed or canceled",
                text: "See console for details",
                icon: "warning"
            });
        }
    };

    const convertToBase64 = async (url: string): Promise<string> => {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                resolve(reader.result as string);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    };

    return <>
        {/* Login Thrid Part */}
        {showLogin && confirmAgree && (
            <section className="w3l-hotair-form fade-out">
                <div className="container">
                    <div className="workinghny-form-grid">
                        <div className={`main-hotair ${showImage ? "main-hotair-with-img" : ""}`}>
                            <div onClick={e => setShowLogin(false)} className="alert-close">
                                <span onClick={e => setShowLogin(false)} className="fa fa-close"></span>
                            </div>
                            <div className={`content-wthree ${!showImage ? "content-wthree-without-img" : ""}`}>
                                <h2>To Connect With Your Social Media</h2>
                                <div className="social-icons w3layouts">
                                    <ul>
                                        <li>
                                            <p onClick={handleFBLogin} className="facebook"><span className="fa fa-facebook"></span> </p>
                                        </li>
                                        <li>
                                            <p className="twitter"><span className="fa fa-phone"></span> </p>
                                        </li>
                                        <li>
                                            <p className="pinterest"><span className="fa fa-weibo"></span> </p>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            {showImage &&
                                <div className="w3l_form align-self">
                                    <div className="left_grid_info">
                                    </div>
                                </div>
                            }
                        </div>
                    </div>
                </div>
                <div className="copyright text-center">
                </div>
            </section>
        )}
    </>
}


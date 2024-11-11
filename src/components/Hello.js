import { useState, useEffect } from "react"
import "./css/style.css"
import "./css/font-awesome.min.css"

export const Hello = ({ updateUsernameCallback, confirmAgree }) => { // outside for set here
    const [showLogin, setShowLogin] = useState(true);
    const [showImage, setShowImage] = useState(window.innerWidth >= 400);
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
            js = d.createElement(s); js.id = id;
            js.src = "https://connect.facebook.net/en_US/sdk.js";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, 'script', 'facebook-jssdk'));


        window.fbAsyncInit = function () {
            window.FB.init({
                appId: '1592228174832411',
                xfbml: true,
                version: 'v21.0' // the-graph-api-version-for-your-app
            });
        };
    }, []);

    const handleFBLogin = () => {
        console.log('Click FB Login');

        if (window.FB) {
            window.FB.login(function (response) {
                if (response.authResponse) {
                    console.log('Welcome!  Fetching your information.... ');
                    window.FB.api('/me', {
                        fields: 'id, name, picture, gender, posts, likes' //me?fields=posts{full_picture,message} 能拿到post中圖片
                    }, async function (responses) {
                        console.log(responses);
                        console.log(responses.picture.data.url);
                        updateUsernameCallback(responses.name);


                        console.log("id", responses.id);
                        
                        let accessToken = response.authResponse.accessToken;
                        console.log('accessToken :', accessToken);

                        // 
                        // const responseOK = await fetch('http://localhost:5000/', {
                        //     method: 'POST',
                        //     headers: {
                        //         'Content-Type': 'application/json'
                        //     },
                        //     body: JSON.stringify({ fbAccessToken: accessToken })
                        // });

                        // console.log('responseOK', responseOK);
                        

                        // change picture to base 64
                        const data = responses.picture.data.url  // https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=523024447160668&height=50&width=50&ext=1733251735&hash=AbZ3mHor3ZeZmBCb4eFd3qC2
                        const base64 = await convertToBase64(data);
                        sessionStorage.setItem('userPicture', base64);

                        console.log('base64', base64);

                        setShowLogin(false)
                    });
                }
            });
        } else {
            console.error('Facebook SDK not loaded');
            setShowLogin(false);
            alert('Error')
        }
    };

    const convertToBase64 = async (url) => {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                resolve(reader.result);
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
                        <div className={`main-hotair ${showImage ? "main-hotair-with-img": ""}`}>
                            <div onClick={e => setShowLogin(false)} className="alert-close">
                                <span onClick={e => setShowLogin(false)} className="fa fa-close"></span>
                            </div>
                            <div className={`content-wthree ${!showImage ? "content-wthree-without-img": ""}`}>
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


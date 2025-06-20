import { useState, useEffect } from "react";

import { UserChatList } from '../../components/ChatMessages';
import { InputControls } from '../../components/Input';
import { Hello } from "../../components/Hello";
import { geolocationApiUrl } from "../../Config";
import './index.css'
import { IFacebookProfile } from "../../components/Interface";
import { userMenuActivationCommand } from "../../Config";

import Swal from "sweetalert2";
import { userMenu } from "../../components/Menu";
import { getSessionInfo } from "../../components/ParamStore";

import { callChatLLMApi, configAnynmousSession } from "../../components/APIService";

import { IMessage } from "../../components/Interface";
import { useNavigate, useSearchParams } from "react-router-dom";

export interface IHome {
    confirmAgree: boolean,
    l2dSpeak: (url: string) => void
}



const Home = ({ confirmAgree, l2dSpeak }: IHome) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [messageList, setMessageList] = useState<IMessage[]>([]);
    const [lastUserMessageMedia, setLastUserMessageMedia] = useState<string[]>([]);
    const [displayHello, setDisplayHello] = useState(true);
    const [userLocationLegent, setUserLocationLegent] = useState("");
    const [locationError, setLocationError] = useState(false);

    const [userMenuActivated, setUserMenuActivated] = useState(false);
    const [userMenuKeys, setUserMenuKeys] = useState<string[]>([]);

    const [facebookProfile, setFacebookProfile] = useState<IFacebookProfile>({
        id: "",
        name: "",
        profilePicture: "",
        gender: "",
        accessToken: ""
    });
    const [username, setUsername] = useState('');
    let throwAccessCodeDialog = () => {
        Swal.fire({
            title: "Please Enter Access Code",
            input: "text",
            text: "The code can be found at the event host or should be provided to you",
            inputAttributes: {
                autocapitalize: "off"
            },
            showDenyButton: true,
            denyButtonText: "Login to continue",
            confirmButtonText: "Continue",
            showLoaderOnConfirm: true,
            allowEscapeKey: false,
            preConfirm: async (code) => {
                try {
                    await configAnynmousSession(code);
                } catch (error) {
                    Swal.showValidationMessage(`Request failed: ${error}`);
                }
            },
            allowOutsideClick: false
        }).then((result) => {
            if (result.isDenied) {
                console.log("redirecting to login")
                navigate("/auth/login")
            }
        });
    };
    useEffect(() => {
        if (facebookProfile.id) {
            console.log(`[Home][useEffect(facebookProfile)] Set facebook profile to\n${JSON.stringify({
                id: facebookProfile.id,
                username: facebookProfile.name
            }, null, 4)}`);
            setUsername(facebookProfile.name);
            return;
        }
    }, [facebookProfile])

    // Check messageList length
    useEffect(() => {
        if (messageList.length > 0) {
            setDisplayHello(false);
        } else {
            setDisplayHello(true);
        }
    }, [messageList]);

    const setMessageMedia = (media: string[]) => {
        console.debug(`[Home][setMessageMedia] Setting Media\n${media.slice(0, 30)}`)
        setLastUserMessageMedia(media);
        setMessageList(prevMessage => {
            const newMessageList = [...prevMessage];
            // remove existing image placeholder
            if (newMessageList.at(-1)?.placeHolder) {
                newMessageList.pop()
            }
            // append image placeholder
            newMessageList.push({
                role: "user",
                media: media,
                placeHolder: true,
            })
            return newMessageList
        });
    }

    const sendMessage = async (messageText: string): Promise<void> => {
        setMessageList(prevMessage => {
            const newMessageList = [...prevMessage];
            if (newMessageList.at(-1)?.placeHolder) {
                newMessageList.pop();
            }
            newMessageList.push({
                role: "user",
                media: lastUserMessageMedia,
                text: messageText,
                time: String(Date().toLocaleString()).split(" ")[4].slice(0, -3),
            });
            return newMessageList;
        });

        let userMenuActivatedState = userMenuActivated;
        if (messageText === userMenuActivationCommand) {
            if (userMenuActivatedState) {
                setUserMenuActivated(false);
                userMenuActivatedState = false;
                setUserMenuKeys([]);
                return;
            } else {
                setUserMenuActivated(true);
                userMenuActivatedState = true;
                const response = await userMenu({
                    input: "",
                    menuKeys: userMenuKeys,
                    setMenuKeys: setUserMenuKeys
                });
                setMessageList(prevMessage => {
                    const newMessageList = [...prevMessage];
                    newMessageList.push({
                        role: "ai",
                        text: response,
                        error: true,
                    });
                    return newMessageList;
                });
                return;
            }
        }

        if (userMenuActivatedState) {
            const response = await userMenu({
                input: messageText,
                menuKeys: userMenuKeys,
                setMenuKeys: setUserMenuKeys,
                setMessageList: setMessageList,
                facebookProfile: facebookProfile,
            });
            setMessageList(prevMessage => {
                const newMessageList = [...prevMessage];
                newMessageList.push({
                    role: "ai",
                    text: response,
                    error: true,
                });
                return newMessageList;
            });
            return;
        }

        // TODO: context
        setMessageList(prevMessage => {
            const newMessageList = [...prevMessage];
            newMessageList.push({ role: "loading", });
            return newMessageList;
        });
        callChatLLMApi({
            content: {
                message: messageText,
                media: lastUserMessageMedia
            },
            location: userLocationLegent
        })
            .then(responseObj => {   // e
                setMessageList(prevMessage => {
                    const newMessageList = [...prevMessage];
                    newMessageList.pop();
                    return newMessageList;
                });
                setMessageList(prevMessage => [
                    ...prevMessage,
                    {
                        role: "ai",
                        text: responseObj.respondMessage,  // e
                        error: false,
                        // context.location = `${location.latitude},${location.longitude}`,
                        time: String(Date().toLocaleString()).split(" ")[4].slice(0, -3),
                    }
                ]);
                if (responseObj.audioBase64 !== "") {
                    l2dSpeak(`data:audio/wav;base64,${responseObj.audioBase64}`);
                }
            })
            .catch(e => {
                console.error(`[Home][sendMessage] Got error from [callChatLLMApi]\n${e}`);
                Swal.fire({
                    title: "Something went wrong",
                    text: e.toString(),
                    icon: 'error',
                })
                setMessageList(prevMessage => {
                    const newMessageList = [...prevMessage];
                    newMessageList.pop();
                    return newMessageList;
                });
                setMessageList(prevMessage => [
                    ...prevMessage,
                    {
                        role: "ai",
                        text: 'Something went wrong',
                        error: true,
                        time: String(Date().toLocaleString()).split(" ")[4].slice(0, -3),
                    }
                ]);
            })
        // Clear contents
        setLastUserMessageMedia([]);
    }

    const getLocation = (): Promise<GeolocationCoordinates> => {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => resolve(position.coords),
                (error) => reject(error),
                {
                    enableHighAccuracy: true,
                    maximumAge: 1000,
                    timeout: 5000,
                }
            );
        });
    };

    useEffect(() => {
        const getAddressFromCoordinates = async () => {
            // 使用 Google Maps Geocoding API
            let addressOutput;
            try {
                if (localStorage.getItem("location")){
                    setLocationError(false);
                    setUserLocationLegent(localStorage.getItem("location"));
                    return;
                }
                const location = await getLocation();
                const addressResponse = await fetch(geolocationApiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: location.latitude,
                        longitude: location.longitude,
                    })
                });
                if (addressResponse.status !== 200) {
                    throw new Error("Failed to fetch address from coordinates");
                }
                const result = await addressResponse.json();
                addressOutput = result.location !== undefined ? result.location : "";
                console.debug(`[Home][useEffect(confirmAgree)][getAddressFromCoordinates] Setting Current User adddress:\n${addressOutput}`);
                setUserLocationLegent(addressOutput);
                setLocationError(false);
            } catch (error) {
                console.error(`[Home][useEffect(confirmAgree)][getAddressFromCoordinates] Error getting user location\n${error}`);
                Swal.fire({
                    title: "Cannot get user location",
                    text: error.toString(),
                    icon: 'error',
                });
                setLocationError(true);
            }
        };
        if (!confirmAgree) {
            return
        }
        getAddressFromCoordinates();
    }, [confirmAgree]);

    useEffect(() => {
        let func = async () => {
            if (getSessionInfo().sessionToken) {
                return
            }
            if (searchParams.has("access_code")) {
                try {
                    await configAnynmousSession(searchParams.get("access_code"));
                } catch {
                    throwAccessCodeDialog();
                }
            } else {
                try {
                    await configAnynmousSession(undefined);
                } catch {
                    throwAccessCodeDialog()
                }
            }
        }
        func()
    })


    return (
        <>
            <UserChatList messageList={messageList} profilePictureUrl={facebookProfile?.profilePicture} />
            <InputControls setMessageMedia={setMessageMedia} sendMessage={sendMessage} clearMessages={() => setMessageList([])} />
            {displayHello && (<div id="hello2">
                <h1 className="title">Hello! {username}</h1>
                <p className="subtitle">How can I help you today?</p>
            </div>)}
            {/* Skip for Innoex Demo */}
            {/* {localStorage.getItem('demo')  !== "true" ? <Hello confirmAgree={confirmAgree} setFacebookProfile={setFacebookProfile} /> : null} */}
            
            <Hello confirmAgree={false} setFacebookProfile={setFacebookProfile} />
            {confirmAgree && !locationError && userLocationLegent !== "" ? <div className="address">用戶位置: {userLocationLegent}</div> : null}
        </>
    )
}

export default Home;
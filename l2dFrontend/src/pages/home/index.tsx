import { useState, useEffect } from "react";

import { UserChatList } from '../../components/ChatMessages';
import { InputControls } from '../../components/Input';
import { Hello } from "../../components/Hello";
import { chatLLMApiUrl, geolocationApiUrl } from "../../Config";
import './index.css'
import { IFacebookProfile } from "../../components/Interface";
import { userMenuActivationCommand } from "../../Config";

import Swal from "sweetalert2";
import { userMenu } from "../../components/Menu";
import { getTTS } from "../../components/LocalStorageParamaters";

export interface IHome {
    confirmAgree: boolean,
    l2dSpeak: (url: string) => void
}

export interface IMessage {
    role: "user" | "ai" | "loading",
    media?: string[],
    placeHolder?: boolean,
    text?: string,
    time?: string,
    error?: boolean,
}

export interface ILLMRequest {
    chatId: string
    content: {
        message: string,
        media: string[]
    },
    location: string,
    context?: object,
    disableTTS?: boolean,
}

export interface ILLMResponse {
    audioBase64: string,
    respondMessage: string,
}


const Home = ({ confirmAgree, l2dSpeak }: IHome) => {
    const [messageList, setMessageList] = useState<IMessage[]>([]);
    const [chatId, setChatId] = useState("");
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

    //inti
    useEffect(() => {
        const initializeApp = async () => {
            setChatId(sessionStorage.getItem('mockChatID') || crypto.randomUUID()); // 114115 crypto.randomUUID()
        };
        initializeApp();
    }, [])

    useEffect(() => {
        if (facebookProfile.id) {
            console.log(`[Home][useEffect(facebookProfile)] Set facebook profile to\n${JSON.stringify({
                id: facebookProfile.id,
                username: facebookProfile.name
            }, null, 4)}`)
            setUsername(facebookProfile.name)
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

    // Fetch from server
    const sendToLLM = async (userMessageObject: ILLMRequest): Promise<ILLMResponse> => {
        console.debug(`[Home][setMessageMedia] Sending request to LLM API\n${JSON.stringify(userMessageObject, null, 4)}`)
        let headers: {
            'Content-Type': string,
            'x-SessionToken'?: string,
        } = {
            'Content-Type': 'application/json',
        }
        if (facebookProfile.sessionId) {
            headers["x-SessionToken"] = facebookProfile.sessionId
        }
        userMessageObject.disableTTS = !getTTS();
        const response = await fetch(chatLLMApiUrl, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(userMessageObject),
        });
        const jsonResponse = await response.json();
        if (response.status !== 200) {
            throw new Error(jsonResponse.detail)
        }
        let responseObject = {
            audioBase64: jsonResponse.ttsAudio ? jsonResponse.ttsAudio : "",
            respondMessage: jsonResponse.message
        }
        console.debug(`[Home][setMessageMedia] Got ok response\n${JSON.stringify(responseObject, null, 4)}`)
        return responseObject // respondMessage
    }

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
                chatId: chatId,
                setChatId: setChatId,
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
        sendToLLM({
            chatId: chatId,
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
                console.error(`[Home][sendMessage] Got error from [sendToLLM]\n${e}`);
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



    return (
        <>
            <UserChatList messageList={messageList} profilePictureUrl={facebookProfile?.profilePicture} />
            <InputControls setMessageMedia={setMessageMedia} sendMessage={sendMessage} clearMessages={() => setMessageList([])} />
            {displayHello && (<div id="hello2">
                <h1 className="title">Hello! {username}</h1>
                <p className="subtitle">How can I help you today?</p>
            </div>)}
            {/* Skip for Innoex Demo */}
            {/* <Hello confirmAgree={confirmAgree} setFacebookProfile={setFacebookProfile} /> */}

            <Hello confirmAgree={false} setFacebookProfile={setFacebookProfile} />
            {confirmAgree && !locationError && userLocationLegent !== "" ? <div className="address">用戶位置: {userLocationLegent}</div> : null}
        </>
    )
}

export default Home;
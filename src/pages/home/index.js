import { useState, useEffect, useRef } from "react";

import { UserChatList } from '../../components/ChatMessages';
import { InputControls } from '../../components/Input';
import { Hello } from "../../components/Hello";
import './index.css'



const Home = ({ confirmAgree, l2dSpeak }) => {
    const [messageList, setMessageList] = useState([]);
    const [chatId, setChatId] = useState("");
    const [lastUserMessageMedia, setLastUserMessageMedia] = useState([]);
    const [displayHello, setDisplayHello] = useState(true);
    const [userName, setUserName] = useState("");
    const [apiUrl, setApiUrl] = useState("");
    const [userLocationLegent, setUserLocationLegent] = useState("");
    const apiUrlRef = useRef(apiUrl);

    const defaultApiUrl = "/api";


    //inti
    useEffect(() => {
        const initializeApp = async () => {
            setChatId(crypto.randomUUID());

            // Initial api url
            const apiUrlInSettings = localStorage.getItem("odhApiUrl");
            const finalApiUrl = apiUrlInSettings || defaultApiUrl;
            setApiUrl(finalApiUrl);
            console.log(finalApiUrl);
            apiUrlRef.current = finalApiUrl;
            // setApiUrl(apiUrlInSettings || defaultApiUrl);
            if (!apiUrlInSettings) {
                localStorage.setItem("odhApiUrl", defaultApiUrl);
            }
        };
        initializeApp();
    }, [defaultApiUrl])


    // Check messageList length
    useEffect(() => {
        if (messageList.length > 0) {
            setDisplayHello(false);
        } else {
            setDisplayHello(true);
        }
    }, [messageList]);

    // Fetch from server
    const sendToLLM = async (userMessageObject) => {
        const response = await fetch(`${apiUrlRef.current}/chat_api`, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userMessageObject),
        });
        const jsonResponse = await response.json();

        let responList = {
            audioBase64: jsonResponse.ttsAudio,
            respondMessage: jsonResponse.message
        }

        // const audioBase64 = jsonResponse.ttsAudio
        // const respondMessage = jsonResponse.message || "No respond"
        return responList // respondMessage
    }

    const setMessageMedia = (media) => {
        console.log(media)
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

    const sendMessage = (messageText) => {
        let message = {
            chatId: chatId,
            role: "user",
            content: {}
        }
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
        message.content.message = messageText
        if (lastUserMessageMedia) {
            message.content.media = lastUserMessageMedia;
        }
        // TODO: context
        setMessageList(prevMessage => {
            const newMessageList = [...prevMessage];
            newMessageList.push({ role: "loading", });
            return newMessageList;
        });
        sendToLLM(message)
            .then(responList => {   // e
                setMessageList(prevMessage => {
                    const newMessageList = [...prevMessage];
                    newMessageList.pop();
                    return newMessageList;
                });
                setMessageList(prevMessage => [
                    ...prevMessage,
                    {
                        role: "ai",
                        text: responList.respondMessage,  // e
                        error: false,
                        // context.location = `${location.latitude},${location.longitude}`,
                        time: String(Date().toLocaleString()).split(" ")[4].slice(0, -3),
                    }
                ]);
                if (responList.audioBase64 !== "") {
                    l2dSpeak(`data:audio/wav;base64,${responList.audioBase64}`);
                }  // 'data:audio/wav;base64,'
            })
            .catch(e => {
                console.error(e);
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

    const getLocation = () => {
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
        if (!confirmAgree) {
            return
        }

        const getAddressFromCoordinates = async () => {

            // 使用 Google Maps Geocoding API
            let addressOutput;
            try {
                const location = await getLocation();
                const addressResponse = await fetch(`${apiUrlRef.current}/api/geocode`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        'location': `${location.latitude},${location.longitude}`
                    })
                });
                const result = await addressResponse.json();
                addressOutput = result.localtion;
            } catch (error) {
                addressOutput = "無法取得地址";
            }
            console.log(addressOutput);
            setUserLocationLegent(addressOutput)
        };

        getAddressFromCoordinates();


    }, [confirmAgree]);



    return (
        <>
            <UserChatList messageList={messageList} />
            <InputControls setMessageMedia={setMessageMedia} sendMessage={sendMessage} clearMessages={e => setMessageList([])} />
            {displayHello && (<div id="hello2">
                <h1 className="title">Hello! {userName}</h1>
                <p className="subtitle">How can I help you today?</p>
            </div>)}
            <Hello updateUsernameCallback={setUserName} confirmAgree={confirmAgree} />
            {confirmAgree && <div className="address">用戶位置: {userLocationLegent}</div>}
        </>
    )
}

export default Home;
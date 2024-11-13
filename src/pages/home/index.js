import { useState, useEffect } from "react";

import { UserChatList } from '../../components/ChatMessages';
import { InputControls } from '../../components/Input';
import { Hello } from "../../components/Hello";
import { defaultApiUrl } from "../../Config";
import './index.css'

import Swal from "sweetalert2";


const Home = ({ confirmAgree, l2dSpeak }) => {
    const [messageList, setMessageList] = useState([]);
    const [chatId, setChatId] = useState("");
    const [lastUserMessageMedia, setLastUserMessageMedia] = useState([]);
    const [displayHello, setDisplayHello] = useState(true);
    const [userLocationLegent, setUserLocationLegent] = useState("");
    const [locationError, setLocationError] = useState(false);

    const [facebookProfile, setFacebookProfile] = useState({});
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
            console.log(`Updating facebook profile to\n${JSON.stringify({
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
    const sendToLLM = async (userMessageObject) => {
        const response = await fetch(`${defaultApiUrl}/chat_api`, { // "/chat_api"
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
                const addressResponse = await fetch(`${defaultApiUrl}/api/geocode`, {
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
                console.log("Current User adddress: \n" + addressOutput);
                setUserLocationLegent(addressOutput);
                setLocationError(false);
            } catch (error) {
                console.error("Error getting user location", error);
                Swal.fire({
                    title: "Cannot get user location",
                    text: "Please make sure you have allowed location access",
                    icon: 'error',
                });
                setLocationError(true);
            }
        };

        getAddressFromCoordinates();


    }, [confirmAgree]);



    return (
        <>
            <UserChatList messageList={messageList} profilePictureUrl={facebookProfile.profilePicture} />
            <InputControls setMessageMedia={setMessageMedia} sendMessage={sendMessage} clearMessages={e => setMessageList([])} />
            {displayHello && (<div id="hello2">
                <h1 className="title">Hello! {username}</h1>
                <p className="subtitle">How can I help you today?</p>
            </div>)}
            <Hello confirmAgree={confirmAgree} setFacebookProfile={setFacebookProfile} apiUrl={defaultApiUrl} />
            {confirmAgree && !locationError ? <div className="address">用戶位置: {userLocationLegent}</div> : null}
        </>
    )
}

export default Home;
import { useState, useRef, useEffect } from "react";

const iconUrl = "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=523024447160668&height=50&width=50&ext=1733220092&hash=Aba9dbz6Cbx1o7uR39R-CLIn"

export const CascatingTextOutput = ({ text }) => {
    const [textDisplayed, setTextDisplayed] = useState('');

    const getRandomDelay = () => 20;// Math.floor(Math.random() * (50 - 10 + 1)) + 10;

    useEffect(() => {
        const setText = async () => {
            let displayTexts = "";
            for (const char of text.split("")) {
                displayTexts += char
                setTextDisplayed(displayTexts);
                await new Promise(resolve => setTimeout(resolve, getRandomDelay()));
            }
        }
        setText();
    }, [text]);

    return (<span>{textDisplayed}</span>);
}


export const App = () => {
    const [apiUrl, setApiUrl] = useState("http://127.0.0.1:5000");
    const [chatId, setChatId] = useState('');
    const [message, setMessage] = useState("");
    const [imageDataUrls, setImageDataUrls] = useState([]);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sendLocation, setSendLocation] = useState(false);
    const fileInputRef = useRef(null);

    const handleImageUpload = (event) => {
        const files = Array.from(event.target.files);
        const promises = files.map(file => {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = (e) => reject(e);
                reader.readAsDataURL(file);
            });
        });

        Promise.all(promises)
            .then(dataUrls => setImageDataUrls(dataUrls))
            .catch(error => console.error("Error reading files: ", error));
    };

    const [userIconBlob, setIconBlob] = useState('');
    const fetchUserIcon = async ({ iconUrl, callBack }) => {
        const data = await fetch(iconUrl);
        const dataBlob = await data.blob();
        const reader = new FileReader();
        reader.onloadend = (e) => {
            callBack(e.target.result);
        };
        reader.readAsDataURL(dataBlob);
    };

    // Init
    useEffect(() => {
        setChatId(crypto.randomUUID());
        fetchUserIcon({ iconUrl: iconUrl, callBack: setIconBlob });
    }, []);

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

    const sendToAPI = async () => {
        setIsLoading(true);
        const humanMessage = { role: "user", content: message, images: imageDataUrls };
        let context = {}
        if (sendLocation) {
            try {
                let location = await getLocation();
                context.location = `${location.latitude},${location.longitude}`
            } catch {
                context.location = "Not Avalable"
            }
        }
        fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                chatId: chatId,
                content: {
                    message: humanMessage.content,
                    images: humanMessage.images,
                },
                context: context,
            }),
        })
            .then(response => response.json())
            .then(data => {
                const aiMessage = { role: "AI", content: data.message, images: [] };
                setMessages([...messages, humanMessage, aiMessage]);
                setMessage('');
                setImageDataUrls([]);
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                }
            })
            .catch(error => console.error("Error sending message: ", error))
            .finally(() => setIsLoading(false));
    };

    return (<>
        <h1>Mock AI API Tester</h1>

        <img src={userIconBlob} alt="shit" />
        <br />
        API Url: <input onChange={e => setApiUrl(e.target.value)} value={apiUrl} />
        <br />
        Chat ID: <input onChange={e => setChatId(e.target.value)} value={chatId} />
        <br />
        Send Location: <input type="checkbox" value={sendLocation} onChange={e => setSendLocation(e.target.value)} />
        <hr />

        Images: <input
            type="file"
            name="myImage"
            multiple
            onChange={handleImageUpload}
            ref={fileInputRef}
        />

        <br />

        Message: <textarea style={{
            verticalAlign: "top",
        }} onChange={e => setMessage(e.target.value)} value={message} />

        <br />

        <button onClick={sendToAPI}>Send</button>

        {isLoading && <p>Loading...</p>}

        <hr />

        <table border={{}}>
            <thead>
                <tr>
                    <th>Role</th>
                    <th>Content</th>
                    <th>Images</th>
                </tr>
            </thead>
            <tbody>
                {messages.map((msg, index) => (
                    <tr key={index}>
                        <td>{msg.role}</td>
                        <td>{<CascatingTextOutput text={msg.content} />}</td>
                        <td>
                            {msg.images.map((url, imgIndex) => (
                                <img key={imgIndex} src={url} alt={`Preview ${imgIndex}`} style={{ maxWidth: "100px", margin: "10px" }} />
                            ))}
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    </>);
}

export default App;
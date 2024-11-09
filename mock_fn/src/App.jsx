import { useState, useRef, useEffect } from "react";
import { imageMapping } from "./components/images";
import { ChatLog } from "./components/ChatLog";
import { FacebookLogin } from "./components/Facebook";


export const App = () => {
    const [apiUrl, setApiUrl] = useState("http://127.0.0.1:5000");
    const [chatId, setChatId] = useState("");
    const [message, setMessage] = useState("");
    const [imageDataUrls, setImageDataUrls] = useState([]);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [sendLocation, setSendLocation] = useState(false);
    const [overideContent, setOverideContent] = useState(false);
    const [tempChatId, setTempChatId] = useState("");
    const fileInputRef = useRef(null);

    const randomIndex = Math.floor(Math.random() * imageMapping.length);

    // Initialize App
    useEffect(() => {
        setChatId(crypto.randomUUID());
    }, []);

    const handleImageUpload = async (event) => {
        try {
            const files = Array.from(event.target.files);
            const promises = files.map(file => {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = (e) => reject(e);
                    reader.readAsDataURL(file);
                });
            });
            const dataUrls = await Promise.all(promises)
            setImageDataUrls([...imageDataUrls, ...dataUrls]);
            fileInputRef.current.value = "";
        } catch (error) {
            console.error("Error reading files: ", error);
        };
    };


    const sendToAPI = async () => {
        setIsLoading(true);
        const humanMessage = { role: "user", content: message, images: imageDataUrls };

        // handle location context
        let context = {};
        if (sendLocation) {
            try {
                const location = await new Promise((resolve, reject) => {
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
                context.location = `${location.latitude},${location.longitude}`;
            } catch {
                context.location = "Not Available";
            }
        }

        // send message to API
        try {
            const response = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    chatId: chatId,
                    content: {
                        message: humanMessage.content,
                        media: humanMessage.images,
                    },
                    context: context,
                    overideContent: overideContent,
                }),
            });
            const respinseData = response.json();
            const aiMessage = { role: "AI", content: respinseData.message, images: [] };
            setMessages([...messages, humanMessage, aiMessage]);
        } catch (error) {
            console.error("Error sending message: ", error);
        };
        setIsLoading(false);
    };

    const handleSetOverideContent = () => {
        setOverideContent(!overideContent);
        if (!overideContent) {
            setTempChatId(chatId);
            setChatId("mock");
        } else {
            setChatId(tempChatId);
        }
    };

    const handleMesasgeAreaPaste = async (e) => {
        e.preventDefault();
        // Paste normal text
        if (e.clipboardData.items[0].type === "text/plain") {
            const text = await new Promise(resolve => e.clipboardData.items[0].getAsString(resolve));
            setMessage(message + text);
            return;
        }
        // Paste image
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            // add video when supported, for now, only images
            if (items[i].type.indexOf("image") !== -1) {
                const blob = items[i].getAsFile();
                const reader = new FileReader();
                reader.onload = (e) => {
                    console.log("pasting image");
                    setImageDataUrls(prevUrls => [...prevUrls, e.target.result]);
                };
                reader.readAsDataURL(blob);
            }
        }
    };

    return (
        <>
            <h1>Mock AI API Tester</h1>
            <img style={{ height: "200px" }} src={imageMapping[randomIndex]} alt="CATS" />
            <hr />
            <h2>Settings</h2>
            API Url: <input onChange={e => setApiUrl(e.target.value)} value={apiUrl} />
            <br />
            Chat ID: <input onChange={e => setChatId(e.target.value)} value={chatId} />
            <br />
            Send Location: <input type="checkbox" name="send location" checked={sendLocation} onChange={e => setSendLocation(e.target.checked)} />
            <br />
            Use Overide: <input type="checkbox" name="overide" checked={overideContent} onChange={handleSetOverideContent} />
            <hr />

            <FacebookLogin />

            <hr />

            <h2>Inputs</h2>
            {imageDataUrls.length > 0 &&
                <>
                    Images Selected:<br></br>
                    {imageDataUrls.map((url, index) => (
                        <img key={index} src={url} alt={`Preview ${index}`} style={{ maxWidth: "30px", marginLeft: "3px" }} />
                    ))}
                    <br />
                </>}
            Images:
            <input type="button" value="Clear" onClick={() => setImageDataUrls([])} />
            <input type="file" multiple onChange={handleImageUpload} ref={fileInputRef} style={{ display: "none" }} />
            <input type="button" value="Select Image" onClick={() => fileInputRef.current.click()} />
            <br />

            Message: <textarea
                onPaste={handleMesasgeAreaPaste}
                style={{ verticalAlign: "top" }}
                onChange={e => setMessage(e.target.value)}
                value={message} />
            <br />

            <button onClick={sendToAPI}>Send</button>
            {isLoading && <p>Loading...</p>}

            <ChatLog messages={messages} />

        </>
    );
};

export default App;
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { imageMapping } from "./images";

export const CascatingTextOutput = ({ text }) => {
    const [textDisplayed, setTextDisplayed] = useState("");

    const getRandomDelay = () => 20;

    useEffect(() => {
        const setText = async () => {
            let displayTexts = "";
            for (const char of text.split("")) {
                displayTexts += char;
                setTextDisplayed(displayTexts);
                await new Promise(resolve => setTimeout(resolve, getRandomDelay()));
            }
        };
        setText();
    }, [text]);

    return <ReactMarkdown>{textDisplayed}</ReactMarkdown>;
};

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
    const [userIconBlob, setIconBlob] = useState("");

    // Initialize App
    useEffect(() => {
        setChatId(crypto.randomUUID());
        // load image
        const randomIndex = Math.floor(Math.random() * imageMapping.length);
        setIconBlob(imageMapping[randomIndex]);
    }, []);

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
            .then(dataUrls => setImageDataUrls([...imageDataUrls, ...dataUrls]))
            .catch(error => console.error("Error reading files: ", error));
        fileInputRef.current.value = "";
    };

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
        let context = {};
        if (sendLocation) {
            try {
                let location = await getLocation();
                context.location = `${location.latitude},${location.longitude}`;
            } catch {
                context.location = "Not Available";
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
                overideContent: overideContent,
            }),
        })
            .then(response => response.json())
            .then(data => {
                const aiMessage = { role: "AI", content: data.message, images: [] };
                setMessages([...messages, humanMessage, aiMessage]);
                setMessage("");
                setImageDataUrls([]);
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                }
            })
            .catch(error => console.error("Error sending message: ", error))
            .finally(() => setIsLoading(false));
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

    return (
        <>
            <h1>Mock AI API Tester</h1>
            <img style={{ height: "200px" }} src={userIconBlob} alt="CATS" />
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
            Message: <textarea onPaste={async (e) => {
                if (e.clipboardData.items[0].type === "text/plain") {
                    const text = await new Promise(resolve => e.clipboardData.items[0].getAsString(resolve));
                    setMessage(message + text);
                    return;
                }
                e.preventDefault();
                const items = e.clipboardData.items;
                for (let i = 0; i < items.length; i++) {
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
            }} style={{ verticalAlign: "top" }} onChange={e => setMessage(e.target.value)} value={message} />
            <br />
            <button onClick={sendToAPI}>Send</button>
            {isLoading && <p>Loading...</p>}

            {messages.length > 0 && <><hr />
                <table border="1">
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
                                <td><CascatingTextOutput text={msg.content} /></td>
                                <td>
                                    {msg.images.map((url, imgIndex) => (
                                        <img key={imgIndex} src={url} alt={`Preview ${imgIndex}`} style={{ maxWidth: "100px", margin: "10px" }} />
                                    ))}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </>}
        </>
    );
};

export default App;
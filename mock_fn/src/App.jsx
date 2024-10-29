import { useState, useRef } from "react";

export const App = () => {
    const [apiUrl, setApiUrl] = useState("http://127.0.0.1:5000");
    const [chatId, setChatId] = useState(crypto.randomUUID());
    const [message, setMessage] = useState("");
    const [imageDataUrls, setImageDataUrls] = useState([]);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
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

    const sendToAPI = () => {
        setIsLoading(true);
        const humanMessage = { role: "user", content: message, images: imageDataUrls };
        fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                chatId: chatId,
                message: humanMessage.content,
                images: humanMessage.images
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

        API Url: <input onChange={e => setApiUrl(e.target.value)} value={apiUrl} />
        <br />
        Chat ID: <input onChange={e => setChatId(e.target.value)} value={chatId} />

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
                        <td>{msg.content}</td>
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
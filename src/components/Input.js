import { useState, useRef } from "react";
import Swal from 'sweetalert2'
import withReactContent from 'sweetalert2-react-content'

const MySwal = withReactContent(Swal)

export const InputControls = ({ setMessageMedia, sendMessage, clearMessages }) => {

    const [text, setText] = useState("");
    // const [media, setMedia] = useState([]);
    // const [showAttachment, setShowAttachment] = useState(false);

    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);

    const inputRef = useRef();

    const clearCurrentState = () => {
        // setMedia([]);
        setText("");
        inputRef.current.blur();
    }

    const handleSendMessage = (e) => {
        e.preventDefault();
        sendMessage(text);
        clearCurrentState();
    }

    const handleClearMessage = (e) => {
        clearCurrentState();
        clearMessages();
    }

    const handleSTT = async (e) => {
        e.preventDefault();

        const sttButton = document.getElementById("stt-button");
        // let mediaRecorder = null;
        // let userMessage = "";
        let audioData = [];

        if (!isRecording) {

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            sttButton.style.backgroundColor = "#f44336";
            const newMediaRecorder = new MediaRecorder(stream);


            newMediaRecorder.ondataavailable = (event) => {
                console.log('stt data', event.data);

                audioData.push(event.data);
                console.log('stt audioChunks', audioData);
            };

            newMediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioData, { type: 'audio/webm' });
                console.log('stt blob', audioBlob);

                // setAudioChunks([]);
                audioData = [];

                // 将 Blob 转换为 Base64
                const reader = new FileReader();
                reader.onloadend = async () => {
                    const base64data = reader.result;
                    console.log('stt base64 ok');


                    const response = await fetch('http://localhost:5000/stt', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ audioData: base64data })
                    });

                    const result = await response.json();
                    console.log('result.message', result.message);
                    // setText(result.message);
                    sendMessage(result.message);
                    console.log('settext', text);
                    // handleSendMessage(result.message);

                };
                reader.readAsDataURL(audioBlob);

                stream.getTracks().forEach(track => track.stop());
                sttButton.style.backgroundColor = "#383838";

            };
            newMediaRecorder.start();
            console.log("start STT");
            setIsRecording(true);
            setMediaRecorder(newMediaRecorder);
            console.log("mediaRecorder", newMediaRecorder);

            sttButton.classList.add('recording');
        } else {

            mediaRecorder.stop();
            console.log("Stop STT");
            setIsRecording(false);
            sttButton.classList.remove('recording');
        }
    };

    const handleFileUpload = () => {
        MySwal.fire({
            title: "Upload images or videos",
            input: "file",
            inputAttributes: {
                "accept": "image/*,video/*",
                'multiple': 'multiple',
                'required': 'required',
                "aria-label": "Upload images or videos",
            },
            icon: 'info',

        })
            // .then(file => { file.value })
            .then(response => {
                console.log(response)
                if (!response.isConfirmed || response.isDismissed) {
                    console.warn("dropped images =")
                    return
                }
                const files = response.value
                if (files.length > 0) {

                    let mediaDataUris = [];

                    let fileReadPromises = [];
                    for (let i = 0; i < files.length; i++) {
                        const file = files.item(i);
                        const reader = new FileReader();
                        const fileReadPromise = new Promise((resolve, reject) => {
                            reader.onloadend = (e) => {
                                console.log("loaded file", file.name);
                                console.log("file preview", e.target.result.slice(0, 10));
                                mediaDataUris.push(e.target.result);
                                resolve();
                            };
                            reader.onerror = reject;
                        });
                        reader.readAsDataURL(file);
                        fileReadPromises.push(fileReadPromise);
                    }

                    Promise.all(fileReadPromises).then(() => {
                        setMessageMedia(mediaDataUris);
                    }).catch(error => {
                        console.error("Error reading files", error);
                    });
                }
            })
    };

    return (
        <div className="typing-area">
            <form action="#" className="typing-form">
                <div className="input-wrapper">
                    <input type="text" ref={inputRef} value={text} onChange={e => setText(e.target.value)} placeholder="Enter a message here" className="typing-input"></input>
                    <button onClick={handleSendMessage} className="icon material-symbols-rounded">send</button>
                </div>
                <div className="action-buttons">
                    <span id="attachment" onClick={handleFileUpload} className="icon material-symbols-rounded">attachment</span>
                    <span id="stt-button" onClick={handleSTT} className="icon material-symbols-rounded">mic</span>
                    <span id="delete-chat-button" className="icon material-symbols-rounded" onClick={handleClearMessage}>delete</span>
                </div>
            </form >
        </div >
    )
}

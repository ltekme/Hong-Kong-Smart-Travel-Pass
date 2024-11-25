import { useState, useRef, ReactElement } from "react";
import { defaultApiUrl, sttApiUrl } from "../Config";
import Swal from 'sweetalert2'
import withReactContent from 'sweetalert2-react-content'

const MySwal = withReactContent(Swal);

export interface IInputControls {
    setMessageMedia: (media: string[]) => void,
    sendMessage: (media: string) => void,
    clearMessages: () => void,
}

export const InputControls = ({
    setMessageMedia,
    sendMessage,
    clearMessages
}: IInputControls): ReactElement => {

    type RecorderState = "recording" | "stopped" | "errored";

    const [text, setText] = useState("");
    const [recorderState, setRecorderState] = useState<RecorderState>("stopped");
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const sttButtonRef = useRef<HTMLSpanElement>(null)
    const inputRef = useRef<HTMLInputElement>(null);

    const clearCurrentState = () => {
        setText("");
        inputRef.current.blur();
    }

    const handleSendMessage = (e: React.MouseEvent<HTMLButtonElement>) => {
        e.preventDefault();
        if (!text) {
            console.warn(`[InputControls][handleSendMessage] Got empty message from input box`);
            MySwal.fire({
                title: "Cannot send empty message",
                icon: 'warning',
            })
            return;
        }
        sendMessage(text);
        clearCurrentState();
    }

    const handleClearMessage = () => {
        clearCurrentState();
        clearMessages();
    }

    const handleSTT = async (e: React.MouseEvent<HTMLSpanElement>) => {
        e.preventDefault();

        const sttButton = document.getElementById("stt-button");
        // let mediaRecorder = null;
        // let userMessage = "";
        let audioData: any[] = [];

        if (!isRecording) {
            let stream: MediaStream;
            let newMediaRecorder;
            let orginalMicInputBgColor = sttButton.style.backgroundColor;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                sttButton.style.backgroundColor = "#f44336";
                newMediaRecorder = new MediaRecorder(stream);
                // handle permission deny
            } catch (error) {
                console.error("Error getting user media", error);
                MySwal.fire({
                    title: "Cannot use microphone input feature",
                    text: "Please allow microphone access to use this feature",
                    icon: 'warning',
                });
                sttButton.style.backgroundColor = orginalMicInputBgColor;
                // sttButton.style.display = "none";
                return;
            }

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

                    let response;
                    try {
                        response = await fetch(sttApiUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ audioData: base64data })
                        });
                    } catch (error) {
                        MySwal.fire({
                            title: "Error processing audio data",
                            icon: 'error',
                        });
                        console.error("Error sending audio data:\n", error);
                        return;
                    }
                    const result = await response.json();
                    console.log('TTS resault message:\n', result.message);
                    setText(ext => {
                        return ext + result.message;
                    });
                    // sendMessage(result.message);
                    console.log('settext', text);
                    // handleSendMessage(result.message);

                };
                reader.readAsDataURL(audioBlob);

                stream.getTracks().forEach(track => track.stop());
                sttButton.style.backgroundColor = orginalMicInputBgColor;

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
            title: "Upload attachments",
            input: "file",
            text: "Upload images, videos or audio",
            inputAttributes: {
                "accept": "image/*,video/*,audio/*",
                'multiple': 'multiple',
                'required': 'required',
                "aria-label": "Upload images, videos or audio",
            },
        })
            // .then(file => { file.value })
            .then(response => {
                if (!response.isConfirmed || response.isDismissed) {
                    console.warn("dropped images =")
                    return
                }
                const files = response.value
                if (files.length > 0) {

                    let mediaDataUris: string[] = [];

                    let fileReadPromises = [];
                    for (let i = 0; i < files.length; i++) {
                        const file = files.item(i);
                        const reader = new FileReader();
                        const fileReadPromise = new Promise<void>((resolve, reject) => {
                            reader.onloadend = (e) => {
                                console.log("loaded file", file.name);
                                console.log("file preview", e.target.result.slice(0, 10));
                                mediaDataUris.push(e.target.result as string);
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
        <div className="typing-area" >
            <form action="#" className="typing-form" >
                <div className="input-wrapper" >
                    <input
                        type="text"
                        ref={inputRef}
                        value={text}
                        onChange={e => setText(e.target.value)}
                        placeholder="Enter a message here"
                        className="typing-input"
                    />
                    < button onClick={handleSendMessage} className="icon material-symbols-rounded" > send </button>
                </div>
                < div className="action-buttons" >
                    < span id="attachment" onClick={handleFileUpload} className="icon material-symbols-rounded" > attachment </span>
                    < span id="stt-button" ref={sttButtonRef} onClick={handleSTT} className="icon material-symbols-rounded" > mic </span>
                    < span id="delete-chat-button" className="icon material-symbols-rounded" onClick={handleClearMessage} > delete </span>
                </div>
            </form >
        </div >
    )
}

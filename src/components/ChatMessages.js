import { useEffect, useState } from "react";

import userImage from "./image/image.jpg";
import aiImage from "./image/gemini.svg";
import ReactMarkdown from 'react-markdown';

export const Chatbox = ({
    message,
    keyIdx,
    profilePictureUrl,
}) => {
    const [delayDisplayText, setDelayDisplayText] = useState("");

    const delayBetweenChar = 20;

    useEffect(() => {
        const setText = async () => {
            // helloTitle.style.display = 'none'
            if (typeof message.text === 'string') {
                let displayTexts = "";
                for (const char of message.text) {
                    displayTexts += char;
                    setDelayDisplayText(displayTexts);
                    await new Promise((resolve) => setTimeout(resolve, delayBetweenChar));
                }
            }
        };
        setText();
    }, [message.text]);

    return (
        // If message.role is loading -> display the loading class (spin avatar image)
        <div key={keyIdx} className={`message incoming${message?.role === "loading" && message?.text === undefined ? " loading" : ""}`}>
            <div className="message-content">
                <img src={message?.role === "ai" || message?.role === "loading" ? aiImage : profilePictureUrl || userImage} alt="AI" className="avatar" />
                <div style={{ display: "inline-block", overflow: "auto" }}>
                    {message.media && message.media.map((content, idx) => {
                        if (content.startsWith("data:image")) {
                            return (<div key={`${keyIdx}-${idx}`}>
                                <img key={keyIdx + "-" + idx} src={content} alt="media" style={{ maxWidth: '80%', maxHeight: '200px' }} />
                            </div>)
                        }
                        if (content.startsWith("data:video")) {
                            return (<div key={`${keyIdx}-${idx}`}>
                                <video key={keyIdx + "-" + idx} controls style={{ maxWidth: '80%', maxHeight: '200px' }} ><source src={content} type="video/mp4" /></video>
                            </div>)
                        }
                        return null;
                    })}
                    {(message.text !== undefined && !message.placeHolder) && <ReactMarkdown className="usertext">{
                        message.role === "user" || message.error ? message.text : delayDisplayText
                    }</ReactMarkdown>}
                </div>
                <div className="time">{message?.role !== "loading" ? message.time : ""}</div>
            </div>
        </div>
    );
}

export const UserChatList = ({
    messageList,
    profilePictureUrl,
}) => {
    return (
        <div id="c2">
            <div className="chat-list">
                {messageList.map((item, idx) => <Chatbox message={item} key={idx} profilePictureUrl={profilePictureUrl} />)}
            </div>
        </div>
    );
}
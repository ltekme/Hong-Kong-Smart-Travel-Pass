import { useEffect, useRef, useState } from "react";
import ReactMarkdown from 'react-markdown';
import { IMessage } from "../pages/home";

export interface IChatBox {
    message: IMessage,
    keyIdx: string,
    profilePictureUrl: string,
    chatListRef: React.MutableRefObject<any>
}
export interface IUserChatList {
    messageList: IMessage[],
    profilePictureUrl: string,
}

export const Chatbox = ({
    message,
    keyIdx,
    profilePictureUrl,
    chatListRef
}: IChatBox) => {
    const [delayDisplayText, setDelayDisplayText] = useState("");
    const userImage = require("./image/image.jpg");
    const aiImage = require("./image/gemini.svg").default;
    useEffect(() => {        
        chatListRef.current.scrollTo({
            top: chatListRef.current.scrollHeight,
            left: 0,
            behavior: "smooth",
        });
    }, [message.text]);

    return (
        // If message.role is loading -> display the loading class (spin avatar image)
        <div key={keyIdx} className={`message incoming${message?.role === "loading" && message?.text === undefined ? " loading" : ""}`}>
            <div className="message-content">
                <img src={message.role === "ai" || message.role === "loading" ? aiImage : profilePictureUrl !== "" ? profilePictureUrl : userImage} alt={message.role} className="avatar" />
                <div style={{ display: "inline-block", overflow: "auto" }}>
                    {message.media && message.media.map((content, idx) => {
                        if (content.startsWith("data:image")) {
                            return (<div key={`${keyIdx}-${idx}`}>
                                <img key={keyIdx + "-" + idx} src={content} alt="media" style={{ maxWidth: '80%', maxHeight: '200px' }} />
                            </div>)
                        }
                        if (content.startsWith("data:video")) {
                            return (<div key={`${keyIdx}-${idx}`}>
                                <video key={keyIdx + "-" + idx} controls style={{ maxWidth: '80%', maxHeight: '200px' }} src={content} />
                            </div>)
                        }
                        if (content.startsWith("data:audio")) {
                            return (<div key={`${keyIdx}-Media${idx}`}>
                                <audio key={keyIdx + "-" + idx} controls src={content} />
                            </div>)
                        }
                        return null
                    })}
                    {(message.text !== undefined && !message.placeHolder) && <ReactMarkdown className={`${message.role}-chat-message usertext`}>{
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
}: IUserChatList) => {

    const chatListRef = useRef(null);

    useEffect(() => {
        chatListRef.current.scrollTo({
            top: chatListRef.current.scrollHeight,
            left: 0,
            behavior: "smooth",
        });
    }, [messageList]);

    return (
        <div id="c2">
            <div className="chat-list" ref={chatListRef}>
                {messageList.map((item, idx) => <Chatbox
                    key={`Chat${idx}`}
                    message={item}
                    keyIdx={`Chat${idx}`}
                    profilePictureUrl={profilePictureUrl}
                    chatListRef={chatListRef}
                />)}
            </div>
        </div>
    );
}
import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

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

export const ChatLog = ({ messages }) => {
    return (
        messages.length > 0 && <><hr />
            <table border="1">
                <thead><tr><th>Role</th><th>Content</th><th>Images</th></tr></thead>
                <tbody>
                    {messages.map((msg, index) => (
                        <tr key={index}>
                            <td>{msg.role}</td>
                            <td>{msg.role === "AI" ?
                                <CascatingTextOutput text={msg.content} />
                                : msg.content
                            }</td>
                            <td>
                                {msg.images.map((url, imgIndex) => (
                                    <img key={imgIndex} src={url} alt={`Preview ${imgIndex}`} style={{ maxWidth: "100px", margin: "10px" }} />
                                ))}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </>
    );
}
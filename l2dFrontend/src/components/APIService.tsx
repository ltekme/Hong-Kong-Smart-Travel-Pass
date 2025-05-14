import { chatLLMchatIDRequestApiUrl, pingUserSessionApiUrl, userPofileAuthApiUrl } from "../Config";
import { IMessage } from "./Interface";
import { getChatId, getSessionInfo, setChatId, setSessionInfo } from "./ParamStore";
import { chatLLMApiUrl } from "../Config";

interface I_UserAuthResoibse {
    sessionToken: string;
    expireEpoch: number;
    username: string;
}

export const getAnonymousUser = async () => {
    const response = await fetch(userPofileAuthApiUrl, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
    });
    if (!response.ok) {
        throw new Error("Failed to fetch anonymous user");
    }
    const data = await response.json();
    return data as I_UserAuthResoibse;
}

export const refreshSession = async () => {
    console.debug(`[APIService] Refreshing session`)
    const sessionInfo = getSessionInfo();
    const response = await fetch(pingUserSessionApiUrl, {
        method: "GET",
        headers: {
            'Content-Type': 'application/json',
            'x-SessionToken': getSessionInfo().sessionToken || "",
        },
    });
    if (!response.ok) {
        throw new Error("Failed to refresh session");
    }
    const data = await response.json();
    setSessionInfo({
        sessionToken: data.sessionToken,
        expireEpoch: data.expireEpoch,
        username: sessionInfo.username,
        kind: sessionInfo.kind,
    });
}

export const configAnynmousSession = async () => {
    console.debug(`[APIService] Configuring anonymous session`)
    const user = await getAnonymousUser();
    console.debug(`[APIService] Got anonymous user\n${JSON.stringify(user, null, 4)}`)
    setSessionInfo({
        sessionToken: user.sessionToken,
        expireEpoch: user.expireEpoch,
        username: user.username,
        kind: "anonymous",
    });
    console.debug(`[APIService] Set session info\n${JSON.stringify(getSessionInfo(), null, 4)}`)
}

export const requestChatLLMApiConversationId = async () => {
    console.debug(`[APIService] Requesting chat ID from server`)
    const response = await fetch(chatLLMchatIDRequestApiUrl, {
        method: "GET",
        headers: {
            'Content-Type': 'application/json',
            'x-SessionToken': getSessionInfo().sessionToken || "",
        },
    });
    const jsonResponse = await response.json();
    if (response.status !== 200) {
        throw new Error(jsonResponse.detail)
    }
    setChatId(jsonResponse.chatId);
}

export const callChatLLMApi = async (param: {
    content: {
        message: string,
        media: string[]
    }
    location: string,
    context?: object,
}) => {
    console.debug(`[APIService] Sending request to LLM API\n${JSON.stringify(param.content.message, null, 4)}`)
    if (!getSessionInfo().sessionToken) {
        console.debug(`[APIService] Session token is not set, configuring anonymous session`)
        await configAnynmousSession();
    }
    if (!getChatId()) {
        console.debug(`[APIService] Chat ID is not set, requesting from server`)
        await requestChatLLMApiConversationId();
    }
    const response = await fetch(chatLLMApiUrl, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'x-SessionToken': getSessionInfo().sessionToken || "",
        },
        body: JSON.stringify({
            chatId: getChatId(),
            content: {
                message: param.content.message,
                media: param.content.media,
            },
            location: param.location,
            context: param.context,
        }),
    });
    const jsonResponse = await response.json();
    if (response.status !== 200) {
        throw new Error(jsonResponse.detail)
    }
    let responseObject = {
        audioBase64: jsonResponse.ttsAudio ? jsonResponse.ttsAudio : "",
        respondMessage: jsonResponse.message
    }
    console.debug(`[APIService] Got ok response\n${responseObject.respondMessage}`)
    await refreshSession();
    console.debug(`[APIService] Updated session info\n${JSON.stringify(getSessionInfo(), null, 4)}`)
    return responseObject as {
        audioBase64: string,
        respondMessage: string,
    }
}
export const setTTS = (val: boolean) => {
    sessionStorage.setItem("enableTTS", val === true ? 'true' : 'false')
}
export const getTTS = () => {
    return sessionStorage.getItem("enableTTS") !== "false"
}

export const clearChatId = () => {
    console.log("[ParamStore] Clearing Chat ID")
    sessionStorage.removeItem("chatId")
}
export const setChatId = (val: string) => {
    if (!val){
        throw Error("cannot use set chat id to clear")
    }
    sessionStorage.setItem("chatId", val)
}

export const getChatId = () => {
    return sessionStorage.getItem("chatId")
}

export const getSessionInfo = () => {
    return {
        sessionToken: sessionStorage.getItem("sessionToken"),
        sessionExpireEpoch: sessionStorage.getItem("sessionExpireEpoch"),
        username: sessionStorage.getItem("username"),
        kind: sessionStorage.getItem("sessionKind"),
    }
}

export const setSessionInfo = (val: {
    sessionToken: string,
    expireEpoch: number,
    username: string,
    kind: string | "anonymous",
}) => {
    sessionStorage.setItem("sessionToken", val.sessionToken)
    sessionStorage.setItem("sessionExpireEpoch", val.expireEpoch.toString())
    sessionStorage.setItem("username", val.username)
    sessionStorage.setItem("sessionKind", val.kind)
}

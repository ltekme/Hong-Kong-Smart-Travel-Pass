export const setTTS = (val: boolean) => {
    localStorage.setItem("enableTTS", val === true ? 'true' : 'false')
}
export const getTTS = () => {
    return localStorage.getItem("enableTTS") !== "false"
}

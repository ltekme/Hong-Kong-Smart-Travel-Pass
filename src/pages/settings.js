import { useEffect, useState } from "react";
import { defaultApiUrl } from "../Config";

export const SettingsPannel = () => {

    const [apiUrl, setApiUrl] = useState(defaultApiUrl);

    useEffect(() => {
        const apiUrlInSettings = localStorage.getItem("ApiUrl");
        setApiUrl(apiUrlInSettings || defaultApiUrl);
        if (!apiUrlInSettings) {
            localStorage.setItem("ApiUrl", defaultApiUrl);
        }
    }, [])

    useEffect(() => {
        localStorage.setItem("ApiUrl", apiUrl);
    }, [apiUrl])

    return (
        <div>
            <h1>Settings</h1>
            <p>Settings go here</p>
            <input type="text" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} />
        </div>
    )
}
import { useEffect, useState } from "react";

const DEFAUTL_API_URL = "http://localhost:5000";

export const SettingsPannel = () => {

    const [apiUrl, setApiUrl] = useState(DEFAUTL_API_URL);

    useEffect(() => {
        const apiUrlInSettings = localStorage.getItem("odhApiUrl");
        setApiUrl(apiUrlInSettings || DEFAUTL_API_URL);
        if (!apiUrlInSettings) {
            localStorage.setItem("odhApiUrl", DEFAUTL_API_URL);
        }
    }, [])

    useEffect(() => {
        localStorage.setItem("odhApiUrl", apiUrl);
    }, [apiUrl])

    return (
        <div>
            <h1>Settings</h1>
            <p>Settings go here</p>
            <input type="text" value={apiUrl} onChange={(e) => setApiUrl(e.target.value)} />
        </div>
    )
}
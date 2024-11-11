
import { useState } from 'react';
import Home from './pages/home';

import useLive2D from "./pages/l2d/hook/useLive2D";
import { LegalDataCollectionNotice } from './pages/LegalDataCollectionNotice/index.jsx';

export const App = () => {
    // const [audioToL2d, setAudioToL2d] = useState("");   
    const [confirmAgree, setConfirmAgree] = useState(false);
    const { speak } = useLive2D();
    return (<>
        <LegalDataCollectionNotice setConfirmAgree={setConfirmAgree} />
        <Home l2dSpeak={speak} confirmAgree={confirmAgree} />
        

        {/* Make Canvise for Live 2d Model */}
        <div style={{ display: "flex", }}>
            <canvas id="can" style={{
                backgroundColor: "#d5d5d5",
            }} />
        </div>
    </>)
}
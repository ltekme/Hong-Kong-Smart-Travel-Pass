import { useRef, useState, useEffect } from 'react';
import Home from './pages/home';
import useLive2D from "./pages/l2d/hook/useLive2D";
import { LegalDataCollectionNotice } from './pages/LegalDataCollectionNotice/index.jsx';
import { enableAvatar } from './Config';


export const App = () => {
    const [confirmAgree, setConfirmAgree] = useState(false);
    const live2dCanvasRef = useRef(null);
    const { speak, initializeModel } = useLive2D();

    useEffect(() => {
        initializeModel({
            avatarCanvus: live2dCanvasRef.current
        });
        setConfirmAgree(true)
    });

    return (<>
        {/* Skip for Innoex Demo */}
        {/* <LegalDataCollectionNotice setConfirmAgree={setConfirmAgree} /> */}

        <Home l2dSpeak={speak} confirmAgree={confirmAgree} />

        {/* Make Canvise for Live 2d Model */}
        <canvas ref={live2dCanvasRef} style={{ display: enableAvatar ? "flex" : "none", }} />
    </>)
}
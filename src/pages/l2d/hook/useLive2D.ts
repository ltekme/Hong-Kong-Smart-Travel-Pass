import { useEffect } from "react";
import * as Define from "../Live2D/Render/Define";
import { Live2DManager } from "../Live2D/Render/Live2DManager";
import { Delegate } from "../Live2D/Render/Delegate";

export default function useLive2D() {

  // Load model
  useEffect(() => {
    Delegate.releaseInstance();

    if (Delegate.getInstance().initialize() === false) {
      return;
    }

    console.log(Delegate.getInstance());


    Delegate.getInstance().run();


    if (Define.CanvasSize === "auto") {
      Delegate.getInstance().onResize();
    }

    const handleResize = () => {
      Delegate.getInstance().onResize();

      const delegate = Delegate.getInstance();

      // const viewportWidth = window.innerWidth;
      if (window.innerWidth >= 450) {

        const translateX = -0.5 * (window.innerWidth / 1000); // 40% 向左平移

        delegate.moveModel(translateX, -0.2

        );
      } else {
        delegate.moveModel(0, -0.37);
      }
    };

    window.addEventListener("resize", handleResize);

    // 初始设置模型位置
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
    };

  }, []);



  // make 
  const speak = async (url: string) => {

    console.log('Moving mouse shit');
    var aud = new Audio(url);
    await aud.play();
    Live2DManager.getInstance().startVoiceConversation(url);
  };

  return { speak }


}


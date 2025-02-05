import { userPofilePersonalizationApiUrl } from "../Config";
import { IFacebookProfile } from "./Interface";

interface UserMenuProps {
    input: string;
    menuKeys: string[];
    setMenuKeys: React.Dispatch<React.SetStateAction<string[]>>;
    chatId?: string;
    setChatId?: React.Dispatch<React.SetStateAction<string>>;
    facebookProfile?: IFacebookProfile;
}

export const userMenu = async ({
    input,
    menuKeys,
    setMenuKeys,
    chatId,
    setChatId,
    facebookProfile,
}: UserMenuProps) => {
    let chatIdDisplay = chatId;

    const Init000 = () => {
        setMenuKeys(["Init000"])
        return "Menu Options\n1. Chat Id\n2. Profile";
    }

    const Init000_1 = () => {
        setMenuKeys(["Init000", "1"]);
        return `Current Chat ID: ${chatIdDisplay}\n1. Change\n2. Back`;
    }

    const Init000_1_1 = () => {
        setMenuKeys(["Init000", "1", "1"]);
        return "Please type new chat id";
    }
    const Init000_1_1_ = () => {
        setChatId(input);
        chatIdDisplay = input;
        return Init000_1();
    }

    const Init000_2 = () => {
        setMenuKeys(["Init000", "2"]);
        return `Current User Profile:\n1. Name\n2. Personalization Summory\n3. Back`;
    }

    const Init000_2_1 = () => {
        setMenuKeys(["Init000", "2", "1"]);
        if (facebookProfile.sessionId === undefined) {
            return "Public Annonmus\n1. Back";
        }
        return `${facebookProfile?.name}\n1. Back`
    }

    const Init000_2_2 = () => {
        setMenuKeys(["Init000", "2", "2"]);
        return `Personalization Summory:\n1. View\n2. Recreate\n3. Edit\n4. Back`
    }

    const Init000_2_2_1 = async () => {
        setMenuKeys(["Init000", "2", "2", "1"]);
        if (facebookProfile.sessionId === undefined) {
            return "Public Annonmus, Not Allowed\n1. Back";
        }

        const response = await fetch(userPofilePersonalizationApiUrl, {
            method: "GET",
            headers: { "x-SessionToken": facebookProfile.sessionId },
        })
        const responseJson = await response.json()
        return `Summary:\n\n${responseJson.summory}\n\nLast Updated:${responseJson.lastUpdate}\n\n1. Back`;
    };

    const Init000_2_2_2 = async () => {
        setMenuKeys(["Init000", "2", "2", "2"]);
        if (facebookProfile.sessionId === undefined) {
            return "Public Annonmus, Not Allowed\n1. Back";
        }
        const response = await fetch(userPofilePersonalizationApiUrl, {
            method: "POST",
            headers: { "x-FacebookAccessToken": facebookProfile.accessToken },
        })
        const responseJson = await response.json()
        return `Summary:\n\n${responseJson.summory}\n\n1. Back`;
    };

    const Init000_2_2_3 = () => {
        setMenuKeys(["Init000", "2", "2", "3"]);
        return "Personalization Edit Place Holder\n1. Back";
    };

    if (menuKeys[0] === "Init000") {  // Main Menu 0
        if (menuKeys[1] === "1") {  // Main Menu -> Chat Id 0_1
            if (menuKeys[2] === "1") { // Main Menu -> Chat Id -> Change 0_1_1
                return Init000_1_1_();
            }
            switch (true) {
                case input === "1":
                    return Init000_1_1();
                case input === "2":
                    return Init000();
            }
        }
        if (menuKeys[1] === "2") {  // Main Menu -> Profile 0_2
            if (menuKeys[2] === "1") {  // Main Menu -> Profile -> Name 0_2_1
                if (menuKeys[3] === "1") { // Main Menu -> Profile -> Name -> Back
                    return Init000_2();
                }
                switch (true) {
                    case input === "1":
                        return Init000_2();
                }
            }
            if (menuKeys[2] === "2") {  // Main Menu -> Profile -> Personalization Summory 0_2_2
                if (menuKeys[3] === "1") {  // Main Menu -> Profile -> Personalization Summory -> View 0_2_2_1
                    if (menuKeys[4] === "1") { // Main Menu -> Profile -> Personalization Summory -> View -> Back 0_2_2
                        return Init000_2_2();
                    }
                    switch (true) {
                        case input === "1":
                            return Init000_2_2();
                    }
                }
                if (menuKeys[3] === "2") {  // Main Menu -> Profile -> Personalization Summory -> Recreate 0_2_2_2
                    if (menuKeys[4] === "1") { // Main Menu -> Profile -> Personalization Summory -> Recreate -> Back 0_2_2
                        return Init000_2_2();
                    }
                    switch (true) {
                        case input === "1":
                            return Init000_2_2();
                    }
                }
                if (menuKeys[3] === "3") {  // Main Menu -> Profile -> Personalization Summory -> Edit 0_2_2_3
                    if (menuKeys[4] === "1") { // Main Menu -> Profile -> Personalization Summory -> Edit -> Back 0_2_2
                        return Init000_2_2();
                    }
                    switch (true) {
                        case input === "1":
                            return Init000_2_2();
                    }
                }
                switch (true) {
                    case input === "1":
                        return Init000_2_2_1(); // Main Menu -> Profile -> Personalization Summory -> View 0_2_2_1
                    case input === "2":
                        return await Init000_2_2_2(); // Main Menu -> Profile -> Personalization Summory -> Recreate 0_2_2_2
                    case input === "3":
                        return Init000_2_2_3(); // Main Menu -> Profile -> Personalization Summory -> Edit 0_2_2_3
                    case input === "4":
                        return Init000_2(); // Main Menu -> Profile 0_2
                }
            }
            switch (true) {
                case input === "1":
                    return Init000_2_1(); // Main Menu -> Profile -> Name 0_2_1
                case input === "2":
                    return Init000_2_2(); // Main Menu -> Profile -> Personalization Summory 0_2_2
                case input === "3":
                    return Init000(); // Main Menu 0
            }
        }
        switch (true) {
            case input === "1":
                return Init000_1(); // Main Menu -> Chat Id 0_1
            case input === "2":
                return Init000_2(); // Main Menu -> Profile 0_2
        }
    }

    return Init000(); // Main Menu 0
}
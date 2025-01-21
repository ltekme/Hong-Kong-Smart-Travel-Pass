interface UserMenuProps {
    input: string;
    menuKeys: string[];
    setMenuKeys: React.Dispatch<React.SetStateAction<string[]>>;
    chatId?: string;
    setChatId?: React.Dispatch<React.SetStateAction<string>>;
}

export const userMenu = ({
    input,
    menuKeys,
    setMenuKeys,
    chatId,
    setChatId,
}: UserMenuProps) => {
    let chatIdDisplay = chatId;

    const Init000 = () => {
        setMenuKeys(["Init000"])
        return "Menu Options\n1. Chat Id\n2. Back";
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

    const Init000_1_2 = () => {
    }

    if (menuKeys[0] === "Init000") {
        if (menuKeys[1] === "1") {
            if (menuKeys[2] === "1") {
                return Init000_1_1_();
            }
            switch (true) {
                case input === "1":
                    return Init000_1_1();
                case input === "2":
                    return Init000();
            }
        }
        switch (true) {
            case input === "1":
                return Init000_1();
        }

    }

    return Init000();
}
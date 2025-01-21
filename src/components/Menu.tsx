
export const userMenu = ({
    menuKeys,
    setMenuKeys,
    input,
}: {
    menuKeys: string[],
    setMenuKeys: React.Dispatch<React.SetStateAction<string[]>>,
    input: string,
}) => {
    let newMenuKeys = [...menuKeys, input] 
    setMenuKeys(newMenuKeys)
    return `Test ${newMenuKeys}`
}
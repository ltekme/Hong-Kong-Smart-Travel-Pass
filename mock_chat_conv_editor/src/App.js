import { useState, useRef } from "react";
import ReactMarkdown from 'react-markdown';
import MDEditor from '@uiw/react-md-editor';

export const App = () => {
  const [chatId, setChatId] = useState('mock');
  const [messages, setMessafe] = useState([]);
  const [newMessageContent, setNewMessageContent] = useState('');
  const [newMessageResponse, setNewMessageResponse] = useState('');
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    const fileName = file.name;
    if (file && fileName.endsWith('.json')) {
      setChatId(fileName.split('_overide')[0]);
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          setMessafe(data.map(msg => ({
            content: msg.question,
            response: msg.response
          })));
        } catch (error) {
          alert('Invalid JSON file');
        }
      };
      reader.readAsText(file, 'utf-8');
    }
    fileInputRef.current.value = null;
  };

  const handleExport = () => {
    const data = JSON.stringify(messages.map((msg) => {
      return {
        question: msg.content,
        response: msg.response,
      }
    }), null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${chatId}_overide.json`;
    a.click();
    a.remove();
  };

  const handleAddMessage = () => {
    if (newMessageContent === "" || !newMessageResponse === "") {
      return;
    }
    setMessafe([...messages, { content: newMessageContent, response: newMessageResponse }]);
    setNewMessageContent('');
    setNewMessageResponse('');
  }


  document.addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 's') {
      // Prevent the Save dialog to open
      e.preventDefault();
      // Place your code here
      handleExport();
    }
  });

  return (<div style={{ margin: "20px" }}>

    {/* Input field */}
    <div>
      <h1>Create mock overide file</h1>
      Chat ID: <br />
      <input value={chatId} onChange={e => setChatId(e.target.value)} /><br />
      Question Match:<br />
      <textarea value={newMessageContent} onChange={e => setNewMessageContent(e.target.value)} placeholder="question match" rows={3} cols={50} /><br />
      Question Standard Response:
      <div data-color-mode="light"><MDEditor value={newMessageResponse} onChange={setNewMessageResponse} height={400} /></div><br />
      <button onClick={handleAddMessage}>Add</button>
      <br />
      <button onClick={handleExport}>export</button>
      <input type="file" accept="application/json" onChange={handleFileUpload} style={{ display: 'none' }} ref={fileInputRef} />
      <button onClick={() => fileInputRef.current.click()}>import</button>
      <button onClick={() => setMessafe([])}>Clear</button>
    </div>

    {/* List of messages */}
    {messages.length > 0 ? <>
      <hr />
      <table>
        <thead><tr><th>Question</th><th>Response</th><th>Action</th></tr></thead>
        <tbody>{messages.map((message, i) => (
          <tr key={i}>
            <td>{message.content}</td>
            <td><ReactMarkdown>{message.response}</ReactMarkdown></td>
            <td>
              <button onClick={() => {
                setMessafe(messages.filter((msg, index) => index !== i));
              }}>Delete</button>
              <button onClick={() => {
                setNewMessageContent(message.content);
                setNewMessageResponse(message.response);
                setMessafe(messages.filter((msg, index) => index !== i));
              }}>Edit</button>
              <button onClick={() => {
                if (i > 0) {
                  const newMessages = [...messages];
                  const temp = newMessages[i - 1];
                  newMessages[i - 1] = newMessages[i];
                  newMessages[i] = temp;
                  setMessafe(newMessages);
                }
              }}>Move Up</button>
              <button onClick={() => {
                if (i < messages.length - 1) {
                  const newMessages = [...messages];
                  const temp = newMessages[i + 1];
                  newMessages[i + 1] = newMessages[i];
                  newMessages[i] = temp;
                  setMessafe(newMessages);
                }
              }}>Move down</button>
            </td>
          </tr>
        ))}
        </tbody>
      </table>
    </> : null}
  </div>)
}

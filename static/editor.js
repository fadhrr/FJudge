var editor = ace.edit("editor");
editor.setTheme("ace/theme/monokai");

// Update editor mode
const testCasesDiv = document.getElementById("test-cases");
const editorDiv = document.getElementById("editor");
const languageSelect = document.getElementById("language");
setEditorMode(languageSelect.value);
languageSelect.addEventListener("change", updateEditorMode);

function updateEditorMode() {
  const selectedLanguage = languageSelect.value;
  setEditorMode(selectedLanguage);
}

function setEditorMode(language) {
  let mode;
  switch (language) {
    case "py":
      mode = "ace/mode/python";
      srcCode = `# Example Source Code\ndef add(a, b):\n    return a + b\n\na = int(input())\nb = int(input())\nprint(add(a,b))`;
      testCases = `[{"input": "2\\n3\\n","output": "5\\n"},{"input": "5\\n3\\n","output": "12\\n"}]`;
      break;
    case "cpp":
      mode = "ace/mode/c_cpp";
      srcCode = `// Example Source Code\n#include <iostream>\n\nusing namespace std;\n\nint main() {\n    int a, b;\n    cin >> a >> b;\n    cout << a + b << endl;\n    return 0;\n}`;
      testCases = `[{"input": "2 3\\n","output": "5\\n"},{"input": "5 7\\n","output": "12\\n"}]`;
      break;
    // Tambahkan case untuk bahasa lain jika diperlukan
    default:
      mode = "ace/mode/text";
  }
  editor.setValue(srcCode);
  testCasesDiv.value = testCases;
  editor.getSession().setMode(mode);
}

const outputContainer = document.getElementById("output-container");
const requestContainer = document.getElementById("request-container");

const runCode = () => {
  const sourceCode = editor.getValue();
  const language = document.getElementById("language").value;
  const testCases = JSON.parse(document.getElementById("test-cases").value);

  const requestBody = {
    source_code: sourceCode,
    language: language,
    test_cases: testCases,
  };

  requestContainer.innerHTML = "<pre>" + JSON.stringify(requestBody, null, 2) + "</pre>";
  outputContainer.innerHTML = "Running...";

  // Kirim permintaan HTTP menggunakan fetch API
  fetch("http://127.0.0.1:8000/api/submission", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(requestBody),
  })
    .then((response) => response.json())
    .then((data) => {
      // Tampilkan hasil eksekusi di output container
      outputContainer.innerHTML =
        "<pre>" + JSON.stringify(data, null, 2) + "</pre>";
    })
    .then(() => {
        editorDiv.style.height.replace = "100%";
    })
    .catch((error) => {
      console.error("Error:", error);
      outputContainer.innerHTML = "<pre>Error: " + error.message + "</pre>";
    });
};

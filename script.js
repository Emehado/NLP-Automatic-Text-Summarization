async function runExtraction() {
  const input = document.querySelector('#upload-zone-1 input');
  const file = input.files[0];

  if (!file) {
    alert("Upload a PDF first");
    return;
  }

  document.getElementById("extract-spinner").style.display = "inline-block";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:8000/extract", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    document.getElementById("extract-spinner").style.display = "none";

    if (data.status === "success") {
      document.getElementById("extract-output").style.display = "block";
      document.getElementById("extracted-text-preview").innerText = data.text;

      document.getElementById("step1-status").innerHTML =
        '<div class="status-dot active"></div> Done';
    } else {
      alert(data.message);
    }

  } catch (err) {
    console.error(err);
    alert("Connection failed");
  }
}


async function runSummarization() {
  const input = document.querySelector('#upload-zone-1 input');
  const file = input.files[0];

  if (!file) {
    alert("Upload a PDF first");
    return;
  }

  document.getElementById("summarize-spinner").style.display = "inline-block";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:8000/summarize", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    document.getElementById("summarize-spinner").style.display = "none";

    if (data.status === "success") {
      const container = document.getElementById("summary-cards-container");

      container.innerHTML = `
        <div class="summary-card">
          <div class="summary-card-header">
            <span class="summary-tag">Summary</span>
          </div>
          <div class="summary-text">${data.summary}</div>
        </div>
      `;
    } else {
      alert(data.message);
    }

  } catch (err) {
    console.error(err);
    alert("Connection failed");
  }
}
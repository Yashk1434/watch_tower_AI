const video = document.getElementById("video");
const statusText = document.getElementById("status");
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");
canvas.width = 320;  // Resize frame to reduce size
canvas.height = 240;
let streaming = false;

// Request webcam access
navigator.mediaDevices.getUserMedia({ video: true, audio: false })
  .then(stream => {
    video.srcObject = stream;
    video.play();
    streaming = true;
  })
  .catch(err => {
    alert("Unable to access camera: " + err);
  });

function getCurrentTimestamp() {
  const now = new Date();
  return now.toLocaleString();
}

// Capture frame and send to server
function captureAndSend() {
  if (!streaming) return;

  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  let imageData = canvas.toDataURL("image/jpeg", 0.6); // Compressed JPEG

  fetch("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ image: imageData })
  })
  .then(res => res.json())
  .then(data => {
    const { label, confidence, violence } = data;

    const timestamp = getCurrentTimestamp();
    statusText.innerText = `🕒 ${timestamp}
Prediction: ${label}
Confidence: ${confidence}`;

    if (violence) {
      video.classList.add("alert");
    } else {
      video.classList.remove("alert");
    }
  })
  .catch(err => {
    console.error("Prediction failed:", err);
  });
}

// Send frame every 1000 ms (1 sec)
setInterval(captureAndSend, 1000);


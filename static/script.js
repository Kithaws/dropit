// Firebase initialization and helper functions for DropIt
// This file is loaded as a module from the HTML templates. It does not
// change any UI/stylesheet rules – it simply attaches listeners and writes
// to your Firebase project so that the client side stays in sync with the
// console database.

// imports from CDN so that no build step is required
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-analytics.js";
import { getFirestore, doc, setDoc, onSnapshot } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-firestore.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyDRtTpOiLvFxGCCJoPoGNauletvpnacalI",
  authDomain: "dropit-f88da.firebaseapp.com",
  projectId: "dropit-f88da",
  storageBucket: "dropit-f88da.firebasestorage.app",
  messagingSenderId: "804792600823",
  appId: "1:804792600823:web:687306a710ef1dc3eeebf2",
  measurementId: "G-KBYGGDV6K8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app); // make sure db is assigned for any functions that need it

// helper functions that write to Firestore. You can add more as needed.
async function createRoomInFirestore(roomId) {
  try {
    await setDoc(doc(db, "rooms", roomId), {
      createdAt: new Date().toISOString()
    });
  } catch (e) {
    console.error("Error creating room in Firestore:", e);
  }
}

async function sendTextToFirestore(roomId, text) {
  try {
    await setDoc(doc(db, "rooms", roomId), { text }, { merge: true });
  } catch (e) {
    console.error("Error sending text to Firestore:", e);
  }
}

// Debounce helper for real-time text updates
function debounce(func, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

// Track active listeners to avoid duplicates
const activeListeners = new Set();

// Upload helper for AJAX file transfers
async function uploadRoomFile(roomId, file) {
  const fd = new FormData();
  fd.append("file", file);
  const resp = await fetch(`/upload/${roomId}`, {
    method: "POST",
    body: fd,
    headers: { "X-Requested-With": "XMLHttpRequest" }
  });
  if (!resp.ok) throw new Error("Upload failed");
  return resp.json(); // expects { fileUrl: "/download/room" }
}

// Render file (image or link) inside #file-display
function renderFile(fileUrl) {
  const display = document.getElementById("file-display");
  if (!display) return;
  display.innerHTML = "";

  // guess by extension if we should show an image
  const ext = fileUrl.split(".").pop().toLowerCase();
  if (["png","jpg","jpeg","gif","bmp","webp"].includes(ext)) {
    const img = document.createElement("img");
    img.src = fileUrl;
    display.appendChild(img);
  } else {
    const a = document.createElement("a");
    a.href = fileUrl;
    a.textContent = "Download file";
    a.target = "_blank";
    display.appendChild(a);
  }
}

// Real-time text + file synchronization across multiple users
window.addEventListener("DOMContentLoaded", () => {
  const textForm = document.querySelector("form[action^='/send-text']");
  const textarea = textForm?.querySelector("textarea[name='text']");
  const fileInput = document.querySelector("input[type='file']");
  const roomId = window.location.pathname.split("/").pop();

  // ensure firestore document exists even if nobody has typed yet
  if (roomId) {
    createRoomInFirestore(roomId);
  }

  if (fileInput && roomId) {
    // normal file selection
    fileInput.addEventListener("change", async () => {
      const file = fileInput.files[0];
      if (file) {
        try {
          const result = await uploadRoomFile(roomId, file);
          await setDoc(doc(db, "rooms", roomId), { fileUrl: result.fileUrl }, { merge: true });
        } catch (e) {
          console.error("File upload error", e);
        }
      }
    });

    // drag & drop support on the surrounding upload-area
    const uploadArea = document.querySelector(".upload-area");
    if (uploadArea) {
      uploadArea.addEventListener("dragover", e => {
        e.preventDefault();
        uploadArea.style.borderColor = "#6b7280";
      });
      uploadArea.addEventListener("dragleave", e => {
        uploadArea.style.borderColor = "#4b5563";
      });
      uploadArea.addEventListener("drop", async e => {
        e.preventDefault();
        uploadArea.style.borderColor = "#4b5563";
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length) {
          const file = dt.files[0];
          try {
            const result = await uploadRoomFile(roomId, file);
            await setDoc(doc(db, "rooms", roomId), { fileUrl: result.fileUrl }, { merge: true });
          } catch (err) {
            console.error("Drag-drop upload failed", err);
          }
        }
      });
    }
  }

  if (textForm && textarea) {
    const roomId = window.location.pathname.split("/").pop();
    
    const debouncedUpdate = debounce(async (text) => {
      if (text.trim()) {
        await sendTextToFirestore(roomId, text);
      }
    }, 500);

    textarea.addEventListener("input", () => {
      const text = textarea.value;
      debouncedUpdate(text);
    });

    textForm.addEventListener("submit", async event => {
      const finalText = textarea.value;
      if (roomId && finalText) {
        await sendTextToFirestore(roomId, finalText);
      }
    });

    if (!activeListeners.has(roomId)) {
      activeListeners.add(roomId);

      onSnapshot(doc(db, "rooms", roomId), (snapshot) => {
        if (snapshot.exists()) {
          const data = snapshot.data();
          const receivedText = data.text || "";
          const fileUrl = data.fileUrl;

          if (receivedText !== textarea.value) {
            textarea.value = receivedText;
          }
          if (fileUrl) {
            renderFile(fileUrl);
          }
        }
      });
    }
  }
});

export { createRoomInFirestore, sendTextToFirestore };
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

// Real-time text synchronization across multiple users
window.addEventListener("DOMContentLoaded", () => {
  const textForm = document.querySelector("form[action^='/send-text']");
  const textarea = textForm?.querySelector("textarea[name='text']");
  
  if (textForm && textarea) {
    const roomId = window.location.pathname.split("/").pop();
    
    // Store original submit handler
    const debouncedUpdate = debounce(async (text) => {
      // Update Firebase as user types (not just on submit)
      if (text.trim()) {
        await sendTextToFirestore(roomId, text);
      }
    }, 500); // Update after 500ms of no typing
    
    // Update Firebase as user types in real-time
    textarea.addEventListener("input", () => {
      const text = textarea.value;
      debouncedUpdate(text);
    });
    
    // Still allow form submission
    textForm.addEventListener("submit", async event => {
      const finalText = textarea.value;
      if (roomId && finalText) {
        await sendTextToFirestore(roomId, finalText);
      }
      // Allow form to submit normally (redirect will clear the page anyway)
    });
    
    // Set up real-time listener if not already active for this room
    if (!activeListeners.has(roomId)) {
      activeListeners.add(roomId);
      
      // Listen for real-time updates from any user and copy into textarea
      onSnapshot(doc(db, "rooms", roomId), (snapshot) => {
        if (snapshot.exists()) {
          const data = snapshot.data();
          const receivedText = data.text || "";
          
          // always update textarea value if it differs; this lets both
          // participants see exactly what the other is currently typing
          if (receivedText !== textarea.value) {
            textarea.value = receivedText;
          }
        }
      });
    }
  }
});

export { createRoomInFirestore, sendTextToFirestore };
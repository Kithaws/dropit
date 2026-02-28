// Firebase initialization and helper functions for DropIt
// This file is loaded as a module from the HTML templates. It does not
// change any UI/stylesheet rules – it simply attaches listeners and writes
// to your Firebase project so that the client side stays in sync with the
// console database.

// imports from CDN so that no build step is required
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-analytics.js";
import { getFirestore, doc, setDoc } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-firestore.js";

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

// optional: hook form submissions so the data is also sent to Firebase
// without modifying the existing UI/behaviour
window.addEventListener("DOMContentLoaded", () => {
  // when a room form is submitted we don't know the id until after redirect,
  // so this listener is mainly illustrative.
  const textForm = document.querySelector("form[action^='/send-text']");
  if (textForm) {
    textForm.addEventListener("submit", async event => {
      const roomId = window.location.pathname.split("/").pop();
      const text = textForm.querySelector("textarea[name='text']").value;
      if (roomId && text) {
        await sendTextToFirestore(roomId, text);
      }
      // let the normal form submit continue to the server
    });
  }
});

export { createRoomInFirestore, sendTextToFirestore };
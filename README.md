# Dropit

## Basic Details

### Team Name: GREEN APPLE

### Team Members
- Member 1: ANASWARA - COLLEGE OF ENGINEERING VADAKARA
- Member 2: SWATHI - COLLEGE OF ENGINEERING VADAKARA

### Hosted Project Link
https://dropit-v4nf.onrender.com

### Project Description
Dropit is a lightweight file and text sharing web application that allows users to create temporary rooms for sharing messages and files in real time. Users can type together and see updates instantly, and files appear across all participants without page reloads.

### The Problem statement
Sharing files and notes quickly between devices or people in the same vicinity often requires installation of apps or physical media. We solve the problem of ad-hoc data transfer without requiring accounts or software installation.

### The Solution
We provide a simple browser-based room system where users can create a room link, open it on multiple devices, and share text and files in real time powered by Firebase and FastAPI. Everything happens in the browser, and rooms expire after a short period for privacy.

---

## Technical Details

### Technologies/Components Used

**For Software:**
- Languages used: JavaScript, Python, HTML, CSS
- Frameworks used: FastAPI (backend), Jinja2 templates (frontend)
- Libraries used: Firebase JS SDK (realtime), qrcode, sqlite3, uvicorn
- Tools used: VS Code, Git, Python virtualenv

**For Hardware:**
- N/A (purely software project)

---

## Features

List the key features of your project:
- Instant real-time text collaboration in a shared room
- Drag-and-drop or click file upload with immediate sharing
- Automatic room expiration for privacy (10 minutes)


---

## Implementation

### For Software:

#### Installation
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Run
```bash
uvicorn main:app --reload
```

---

## Project Documentation

### For Software:

#### Screenshots (Add at least 3)

!<img width="1365" height="678" alt="Screenshot 2026-02-28 090350" src="https://github.com/user-attachments/assets/db56e1e0-0380-4d56-a77f-131c6b619b6b" />
(Add screenshot 1 here with proper name)
*Landing page with create room button*

!<img width="1365" height="767" alt="Screenshot 2026-02-28 090502" src="https://github.com/user-attachments/assets/d44f63fa-fcaf-40e6-a76e-152ed5c18930" />

*Room page showing text area and upload area*

!<img width="1308" height="707" alt="Screenshot 2026-02-28 090609" src="https://github.com/user-attachments/assets/f92d4255-ba11-4e1c-abd4-f9f6592050bd" />

*File shared appears instantly across windows*
### Demo Video
Watch the demo video here: https://drive.google.com/drive/folders/1s1p3AtZaEt1sjpFkStXVdjrZ9gZBpLvz

#### Diagrams

**System Architecture:**

!<img width="1247" height="900" alt="diagram-export-28-2-2026-9_31_13-am" src="https://github.com/user-attachments/assets/5f2bab4b-4cb2-4b02-9af8-8eed912970e3" />

*Explain your system architecture - components, data flow, tech stack interaction*

**Application Workflow:**

!<img width="795" height="1769" alt="diagram-export-28-2-2026-9_35_32-am" src="https://github.com/user-attachments/assets/7f1c6b12-3465-4689-9c32-bebe35f9053f" />

*Add caption explaining your workflow*

---

### For Web Projects with Backend:

#### API Documentation

**Base URL:** `https://dropit-v4nf.onrender.com/`

##### Endpoints

**GET /**
- **Description:** Returns the home page with create room button
- **Response:** HTML page

**POST /create-room**
- **Description:** Generates a new room ID and redirects to room page

**GET /room/{room_id}**
- **Description:** Returns the room interface with text and file sharing
- **Parameters:** `room_id` (string) – unique identifier for the room

**POST /upload/{room_id}**
- **Description:** Accepts file upload; stores it and updates room database
- **Response:** Redirect or JSON (for AJAX)

**POST /send-text/{room_id}**
- **Description:** Saves text to room database

**GET /download/{room_id}**
- **Description:** Retrieves uploaded file and schedules room deletion

---

### For Mobile Apps:

#### App Flow Diagram

!<img width="1429" height="783" alt="diagram-export-28-2-2026-10_13_16-am" src="https://github.com/user-attachments/assets/d5d4fb2f-db7a-4773-9d9e-0f8514bb180a" />

*Explain the user flow through your application*

---

### Additional Documentation

### AI Tools Used (Optional - For Transparency Bonus)

**Tool Used:** GitHub Copilot, ChatGPT (Raptor mini), Eraser

**Purpose:**
- Generated boilerplate and refactored Python/JavaScript code
- Assisted with real-time collaboration logic and CSS styling
- Created Architecture diagrams from already existing plan

**Key Prompts Used:**
- "Create a FastAPI endpoint for file upload and JSON response"
- "Implement real-time text sharing with Firebase"

**Percentage of AI-generated code:** ~40%

**Human Contributions:**
- Architecture design and planning
- Custom business logic implementation
- Integration and testing
- UI/UX design decisions

---



## Team Contributions

- SWATHI: Backend development, Firebase integration, real-time synchronization
- ANASWARA: Frontend layout, UI styling, 

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ at TinkerHub

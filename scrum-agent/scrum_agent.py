import streamlit as st
import anthropic
import json
import xlwings as xw

client = anthropic.Anthropic(api_key="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")

# File mapping for each employee
EMPLOYEE_FILES = {
    "brady semple": "C:/Users/laiba/Downloads/MpalChatbot/Project Tracker - Brady Semple.xlsm",
    "kristin bennett": "C:/Users/laiba/Downloads/MpalChatbot/Project Tracker - Kristin BennettV3testing.xlsm",
}

st.set_page_config(page_title="MMRI Scrum Agent", page_icon="🤖")
st.title("🤖 MMRI Daily Scrum Agent")
st.caption("Your 2-minute daily project update assistant")

if "conversation" not in st.session_state:
    st.session_state.conversation = []
    st.session_state.updates = {}
    st.session_state.started = False
    st.session_state.updates_ready = False

SYSTEM_PROMPT = """You are a friendly scrum agent for the MMRI lab at McMaster University. 
Your job is to conduct a quick 2-minute daily standup with each employee.

Ask these questions one at a time in a friendly conversational way:
1. What is your name?
2. Are you updating an existing project or adding a new project?

If UPDATING an existing project, ask:
- Which project code?
- What is your current % complete?
- How many hours did you spend on it today?
- What is the status? (In Progress, Future Work, or Complete)
- Any blockers or risks?

If adding a NEW project, ask:
- Project code?
- Task name?
- Start date?
- End date?
- Estimated hours?
- Current status? (In Progress, Future Work, or Complete)
- Current % complete?
- Hours complete so far?
- Priority? (High, Medium, Low)
- Any blockers or risks?

You can handle multiple projects in one session. After each project ask "Any other projects to update or add?"

Once done with all projects say UPDATES_COMPLETE.

Be friendly, concise and professional. Keep responses short."""

for message in st.session_state.conversation:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if not st.session_state.started:
    if st.button("Start Daily Scrum"):
        st.session_state.started = True
        opening = "Hi! I'm your MMRI Scrum Agent 👋 I'll help you log your daily project updates in about 2 minutes. Let's get started!\n\nFirst, what's your name?"
        st.session_state.conversation.append({"role": "assistant", "content": opening})
        st.rerun()

user_input = st.chat_input("Type your response here...")

if user_input and st.session_state.started:
    st.session_state.conversation.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=st.session_state.conversation
            )
            assistant_message = response.content[0].text
            st.write(assistant_message)

    st.session_state.conversation.append({"role": "assistant", "content": assistant_message})

    if "UPDATES_COMPLETE" in assistant_message:
        st.session_state.updates_ready = True

if st.session_state.get("updates_ready"):
    st.success("✅ Updates collected! Ready to export to Excel.")
    if st.button("Export to Excel"):
        with st.spinner("Extracting and exporting..."):
            extraction_response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Based on this scrum conversation, extract the project updates in JSON format:
                    
{str(st.session_state.conversation)}

Return ONLY a JSON object like this, no other text:
{{
    "employee_name": "name here",
    "updates": [
        {{
            "type": "update",
            "project_code": "code",
            "status": "In Progress/Future Work/Complete",
            "percent_complete": 50,
            "hours_today": 2,
            "blockers": "any blockers or none"
        }}
    ],
    "new_projects": [
        {{
            "type": "new",
            "project_code": "code",
            "task": "task name",
            "start_date": "DD/MM/YYYY",
            "end_date": "DD/MM/YYYY",
            "estimated_hours": 100,
            "status": "In Progress/Future Work/Complete",
            "percent_complete": 0,
            "hours_complete": 0,
            "priority": "High/Medium/Low",
            "blockers": "any blockers or none"
        }}
    ]
}}"""
                }]
            )

            st.write("Raw response:", extraction_response.content[0].text)

            try:
                raw_text = extraction_response.content[0].text
                clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)
                st.success("✅ Updates extracted!")
                st.json(data)

                employee_name = data["employee_name"].lower()
                file_path = EMPLOYEE_FILES.get(employee_name)

                if not file_path:
                    st.error(f"No Excel file found for {data['employee_name']}.")
                else:
                    wb = xw.Book(file_path)
                    ws = wb.sheets["ProjectTracker"]
                    st.write("Sheet found! Last used row:", ws.cells(200, 1).end('up').row)

                    for update in data.get("updates", []):
                        for row in range(12, 200):
                            cell_value = ws.cells(row, 1).value
                            if cell_value == update["project_code"]:
                                ws.cells(row, 8).value = update["status"]
                                ws.cells(row, 9).value = update["percent_complete"] / 100
                                ws.cells(row, 10).value = ws.cells(row, 10).value + update["hours_today"]
                                if update["blockers"] and update["blockers"].lower() != "none":
                                    ws.cells(row, 11).value = update["blockers"]
                                break

                    for new_proj in data.get("new_projects", []):
                        for row in range(12, 200):
                            if ws.cells(row, 1).value is None:
                                ws.cells(row, 1).value = new_proj["project_code"]
                                ws.cells(row, 2).value = new_proj["task"]
                                ws.cells(row, 4).value = new_proj["start_date"]
                                ws.cells(row, 5).value = new_proj["end_date"]
                                ws.cells(row, 6).value = new_proj["estimated_hours"]
                                ws.cells(row, 7).value = new_proj["status"]
                                ws.cells(row, 8).value = new_proj["percent_complete"] / 100
                                ws.cells(row, 9).value = new_proj["hours_complete"]
                                ws.cells(row, 10).value = new_proj["priority"]
                                if new_proj["blockers"] and new_proj["blockers"].lower() != "none":
                                    ws.cells(row, 11).value = new_proj["blockers"]
                                break

                    wb.save()
                    st.success(f"✅ Excel file updated for {data['employee_name']}!")
                    st.session_state.updates_ready = False

            except Exception as e:
                st.error(f"Could not update Excel file: {e}")
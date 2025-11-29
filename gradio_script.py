"""
Copyright 2025 Google LLC
Licensed under the Apache License, Version 2.0
"""

import gradio as gr
import asyncio
from orchestrator import personal_shopper
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event
from typing import AsyncIterator
from google.genai import types

import logging
import json
import os

APP_NAME = "e_commerce_shopper_app"
USER_ID = "default_user"
SESSION_ID = "default_session"
SESSION_SERVICE = InMemorySessionService()
E_COMMERCE_SHOPPER_AGENT_RUNNER = Runner(
    agent=personal_shopper,
    app_name=APP_NAME,
    session_service=SESSION_SERVICE,
)


async def get_response_from_agent(
    message: str,
    log_history: list[str] = None,
    chat_history: list[tuple[str, str]] = None,
):

    chat_history = chat_history or []
    updated_chat = chat_history + [(message, None)]

    # Yield instantly with new user message and cleared input
    yield (
        gr.update(choices=None),
        updated_chat,
        gr.HTML(""),  # no progress yet
        gr.update(value="", interactive=False, placeholder="Processing..."),
        gr.update(value={}),
        gr.update(value=""),
    )

    await asyncio.sleep(0)  # allow UI to update before backend starts

    log_history = log_history or []
    chat_history = chat_history or []

    progress_value = 0.1
    # As we have 4 agents, every agents increases the progess by 25%
    progress_increment = 0.25

    # Initial yield to show progress
    progress_html = f"""
    <div style='margin-top:8px; display:flex; flex-direction:column; gap:6px;'>
        <div style='display:flex; align-items:center; gap:6px;'>
            <div class='spinner'></div>
            <label><b>Processing User Query...</b></label>
        </div>
        <div style='display:flex; align-items:center; gap:8px;'>
            <progress value='{progress_value}' max='1' 
                style='width:100%; height:12px; accent-color: solid orange;'></progress>
            <span style='min-width:40px; text-align:right; font-weight:bold; color:#444;'>
                {(progress_value*100):.0f}%
            </span>
        </div>
    </div>
    """

    # Refresh dropdown only at the start of a new query
    yield (
        gr.update(choices=[]),  # clear dropdown before starting
        [],  # keep chat
        gr.HTML(progress_html),
        "",  # clear input box
        {},  # reset delegated outputs
        "",  # clear delegation info
    )
    await asyncio.sleep(0.05)

    await SESSION_SERVICE.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    events_iterator: AsyncIterator[Event] = E_COMMERCE_SHOPPER_AGENT_RUNNER.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(role="user", parts=[types.Part(text=message)]),
    )

    delegated_outputs = {}
    delegated_outputs["last_user_message"] = message
    log_response = []  # fresh dropdown entries
    final_response = ""
    log_messages = []

    progress_value = 0.1
    progress_increment = 0.25

    async for event in events_iterator:
        progress_value = min(progress_value + progress_increment, 1.0)
        responses = []
        agent_name = getattr(event, "author", None) or event.__dict__.get("author")

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    responses.append(part.text)
                    final_response = part.text

        text_response = "\n".join(responses).strip()
        if not text_response:
            continue

        # Always store the agent’s response
        delegated_outputs[agent_name] = text_response

        # Maintain internal-to-readable mapping
        if "_agent_name_map" not in delegated_outputs:
            delegated_outputs["_agent_name_map"] = {}

        readable_name = agent_name.replace("_", " ").title()
        delegated_outputs["_agent_name_map"][readable_name] = agent_name  # reverse map

        if readable_name not in log_response:
            log_response.append(readable_name)
            log_messages.append(f"\n⚙️ Delegated To: {readable_name}")

        # Custom progress bar with spinner
        progress_html = f"""
        <div style='margin-top:8px; display:flex; flex-direction:column; gap:6px;'>
            <div style='display:flex; align-items:center; gap:6px;'>
                <div class='spinner'></div>
                <label><b>Received Response from {readable_name}...</b></label>
            </div>
            <div style='display:flex; align-items:center; gap:8px;'>
                <progress value='{progress_value}' max='1' 
                    style='width:100%; height:12px; accent-color: orange;'></progress>
                <span style='min-width:40px; text-align:right; font-weight:bold; color:#444;'>
                    {(progress_value*100):.0f}%
                </span>
            </div>
        </div>
        """

        yield (
            gr.update(choices=log_response, value=readable_name),  # use readable name
            chat_history + [(message, text_response)],
            gr.HTML(progress_html),
            "",  # clear textbox
            delegated_outputs,
            "\n".join(log_messages),
        )

    # Final yield
    progress_html = """
    <div style='margin-top:8px; display:flex; flex-direction:column; gap:6px;'>
        <div style='display:flex; align-items:center; gap:6px;'>
            <div class='checkmark'></div>
            <label><b>Response Generated Successfully!</b></label>
        </div>
        <div style='display:flex; align-items:center; gap:8px;'>
            <progress value='1' max='1' 
                style='width:100%; height:12px; accent-color: green;'></progress>
            <span style='min-width:40px; text-align:right; font-weight:bold; color:green;'>100%</span>
        </div>
    </div>
    """

    yield (
        gr.update(choices=log_response, value=readable_name),
        chat_history + [(message, final_response)],
        gr.HTML(progress_html),
        gr.update(
            value="", interactive=True, placeholder="Type your next question here..."
        ),
        delegated_outputs,
        "\n".join(log_messages),
    )


def show_delegated_output(selected_agent, delegated_outputs):
    """Show both the user query and the selected agent's response."""

    # Fetch the most recent user query from delegated_outputs (if stored)
    user_query = delegated_outputs.get("last_user_message", "User query not recorded.")
    agent_name_map = delegated_outputs.get("_agent_name_map", {})
    internal_agent_name = agent_name_map.get(selected_agent, selected_agent)
    agent_output = delegated_outputs.get(internal_agent_name, "No response found.")

    return [(user_query, f"{agent_output}")]


css = """
#ecommerce-heading {text-align: center; margin-bottom: 10px;}
#chat-col {display: flex; flex-direction: column; height: 100vh;}
#chat-box {flex-grow: 1; overflow-y: auto; border: 1px solid #ddd; border-radius: 10px; padding: 8px;}
#msg-box {margin-top: auto;}

/* Spinner animation */
.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid orange;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
"""

with gr.Blocks(css=css) as demo:
    with gr.Row():

        # Left column - delegation log
        with gr.Column(scale=1):
            gr.Markdown("### Delegation Log")
            delegation_info = gr.Markdown(value="")  # visible log above dropdown
            log_box = gr.Dropdown(
                label="Remote Agents Response",
                choices=[],
                interactive=True,
                value=[],
                allow_custom_value=True,
            )
            progress_html = gr.HTML("")  # progress bar sits below dropdown

        # Right column - chat
        with gr.Column(scale=3, elem_id="chat-col"):
            gr.Markdown("### E Commerce Personal Shopper", elem_id="ecommerce-heading")
            gr.Markdown(
                "An e-commerce shopping assistant that finds products, compares prices, and analyzes reviews using real-time scraped data."
            )
            chat_box = gr.Chatbot(elem_id="chat-box")
            # progress_html = gr.HTML("")
            msg = gr.Textbox(label="Your message", elem_id="msg-box")

    delegated_outputs_state = gr.State({})

    # When user sends message
    msg.submit(
        get_response_from_agent,
        [msg, log_box, chat_box],
        [
            log_box,
            chat_box,
            progress_html,
            msg,
            delegated_outputs_state,
            delegation_info,
        ],
    )

    log_box.change(
        show_delegated_output,
        [log_box, delegated_outputs_state],
        chat_box,
    )

demo.launch(server_name="0.0.0.0", server_port=8081)

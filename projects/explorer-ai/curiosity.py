# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from fasthtml.common import *
from starlette.responses import RedirectResponse
from starlette.websockets import WebSocketState
from chat_agent import get_agent, get_checkpoint
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from openai import BadRequestError
from dataclasses import dataclass
from datetime import datetime
import textwrap
import shortuuid
import asyncio
import sqlite3

# Site Map
# / entry page, redirects to /{uuid} with a fresh uuid
# /{uuid} shows the chat history of chat {uuid}, the uuid is used as thread_id for langgraph
#
# datamodel
# (user) 1-n> (chats) 0-n> (cards / stored in LangGraph db)

# model that will be used for generation of next answer
selected_model = "nvdev/meta/llama-3.1-405b-instruct"
# list of supported models the use can choose from
models = {
    "nvdev/meta/llama-3.1-405b-instruct": "NVIDIA NIMs Llama 3.1 405B",
    "nvdev/meta/llama-3.2-3b-instruct": "NVIDIA NIMs Llama 3.2 3B",
    "nvdev/meta/llama-3.3-70b-instruct": "NVIDIA NIMs Llama 3.3 70B"
}

# persistent storage of chat sessions
db = database("data/curiosity.db")
chats = db.t.chats
if chats not in db.t:
    chats.create(id=str, title=str, updated=datetime, pk="id")
ChatDTO = chats.dataclass()

# Patch ChatDTO class with ft renderer and ID initialization
@patch
def __ft__(self: ChatDTO):  # type: ignore
    return Li(
        A(
            textwrap.shorten(self.title, width=60, placeholder="..."),
            id=self.id,
            href=f"/chat/{self.id}",
        ),
        dir="ltr",
    )

# FIXME: this patch does not work, requires fixing
@patch
def __post_init__(self: ChatDTO):  # type: ignore
    self.id = shortuuid.uuid()

# default chat for new chats
new_chatDTO = ChatDTO()
new_chatDTO.id = shortuuid.uuid()

@dataclass
class ChatCard:
    question: str
    content: str
    model_id: str = None
    busy: bool = False
    sources: List = None
    images: List = None
    id: str = ""

    def __post_init__(self):
        self.id = shortuuid.uuid()

    def __ft__(self):
        return Card(
            (
                Progress()
                if self.busy
                else Div(
                    self.content,
                    style="white-space: pre-wrap;",
                )
            ),
            (
                Grid(*[A(Img(src=image), href=image) for image in self.images])
                if self.images and len(self.images) > 0
                else None
            ),
            id=self.id,
            header=Div(
                Strong(self.question), Small(self.model_id, cls="pico-color-grey-200")
            ),
            footer=(
                None
                if self.sources == None
                else Grid(
                    *[
                        Div(A(search_result["title"], href=search_result["url"]))
                        for search_result in self.sources
                    ]
                )
            ),
        )

# FastHTML includes the "HTMX" and "Surreal" libraries in headers, unless you pass `default_hdrs=False`.
app, rt = fast_app(
    live=True,  # type: ignore
    hdrs=(
        picolink,
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.colors.min.css",
            type="text/css",
        ),
        Meta(name="color-scheme", content="light dark"),
        MarkdownJS(),
    ),
    ws_hdr=True,  # web socket headers
)

def navigation():
    navigation = Nav(
        Ul(Li(Hgroup(H3("Explorer AI: Curiosity-Driven Agents"), P("Running on NVIDIA NIMs")))),
        Ul(
            Li(
                Button(
                    "New chat",
                    cls="secondary",
                    onclick=f"window.location.href='/chat/{new_chatDTO.id}'",
                )
            ),
            Li(model_selector()),
            Li(question_list()),
            Li(clear_chathistory()),
        ),
    )
    return navigation

def has_no_answers(chat_id: str):
    # This function checks if there are no answers in the answer_list
    answer_div = answer_list(chat_id)
    return len(answer_div.children) == 0 if hasattr(answer_div, 'children') else True

def question(chat_id: str):
    # Check if there are no answers
    show_p = has_no_answers(chat_id)
    # Define the P component
    p_component = P("Explorer AI: Curiosity-Driven Agents is a project focused on creating interactive agents using large language models (LLMs) within a ReAct architecture. It allows users to interact with models running on NVIDIA NIMs like Llama 3.1 while incorporating search tools to enhance response generation. The project emphasizes modularity, enabling seamless swapping between LLMs and tool-augmented interactions, all within a web-based interface powered by technologies like LangGraph and FastHTML. Its goal is to experiment with agent-based AI systems, offering a dynamic platform for exploring AI-driven conversational agents.", id="p-component") if show_p else None
    question_div = Div(
        Search(
            Group(
                Input(
                    id="new-question",
                    name="question",
                    autofocus=True,
                    placeholder="Ask your question here...",
                    autocomplete="off",
                ),
                Button("Answer", id="answer-btn", cls="hidden-default", onclick="hidePComponent()"),
            ),
            hx_post=f"/chat/{chat_id}",
            target_id="answer-list",
            hx_swap="afterbegin",
            id="search-group",
        ),
        P("\n"), p_component,
    )

    script = Script("""
      function hidePComponent() {
        var pComponent = document.getElementById('p-component');
        if (pComponent) {
          pComponent.style.display = 'none';
        }
      }
    """)

    return Div(question_div, script)

@app.get("/clear_chathistory")
async def clear_chathistory():
    # Connect to the database
    conn = sqlite3.connect("data/curiosity.db")
    cursor = conn.cursor()

    # SQL command to delete all records from the chats table
    delete_query = "DELETE FROM chats"

    # Execute the delete command
    cursor.execute(delete_query)

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()

    return RedirectResponse(url=f"/chat/{new_chatDTO.id}")

def clear_chathistory():
    return Button(
                    "Clear all history",
                    cls="secondary",
                    onclick="window.location.href='/clear_chathistory';",
                )

def question_list():
    return Details(
        Summary("Your last 25 chats"),
        Ul(*chats(order_by="updated DESC", limit=25), dir="rtl"),
        id="question-list",
        cls="dropdown",
        hx_swap_oob="true",
    )

def answer_list(chat_id: str):
    # restore message histroy for current thread
    checkpoint = get_checkpoint(chat_id)
    if checkpoint != None:
        top = None
        content = None
        model_id = None
        sources = None
        images = None
        old_messages = []
        for msg in checkpoint["channel_values"]["messages"]:
            if isinstance(msg, HumanMessage):
                if top != None and content != None:
                    old_messages.append(
                        ChatCard(
                            question=top,
                            content=content,
                            model_id=model_id,
                            sources=sources,
                            images=images,
                        )
                    )
                    top, content, model_id, sources, images = (
                        None,
                        None,
                        None,
                        None,
                        None,
                    )
                top = msg.content
            elif isinstance(msg, AIMessage):
                if "tool_calls" in msg.additional_kwargs:
                    # this is an AIMessage with tool calls. skip
                    continue
                else:
                    content = msg.content
                    model_id = msg.response_metadata["model_name"]
            elif isinstance(msg, ToolMessage) and "results" in msg.artifact:
                sources = msg.artifact["results"]
                images = msg.artifact["images"]
        if top != None and content != None:
            old_messages.append(
                ChatCard(
                    question=top,
                    content=content,
                    model_id=model_id,
                    sources=sources,
                    images=images,
                )
            )
        old_messages.reverse()
        answer_list = Div(*old_messages, id="answer-list")
    else:
        # no previous interaction, so show empty list
        answer_list = Div(id="answer-list")
    return answer_list

def model_selector():
    return Details(
        Summary("Model"),
        Ul(
            *[
                Li(
                    Label(
                        title,
                        Input(
                            name="model",
                            type="radio",
                            value=key,
                            **{"checked": key == selected_model},
                            hx_target="#model",
                            hx_swap="outerHTML",
                            hx_get="/model",
                        ),
                    ),
                    dir="ltr",
                )
                for key, title in models.items()
            ],
            dir="rtl",
        ),
        id="model",
        cls="dropdown",
    )

@rt("/model")
async def get(model: str):
    global selected_model
    if model in models.keys():
        selected_model = model
    return model_selector()

@rt("/")
async def get():
    return RedirectResponse(url=f"/chat/{new_chatDTO.id}")

@rt("/chat/{id}")
async def get(id: str):
    try:
        if id == new_chatDTO.id:
            chat = new_chatDTO
        else:
            chat = chats[id]
    except NotFoundError:
        # TODO need to rewrite URL if id != new_ChatDTO.id
        chat = new_chatDTO

    body = Body(
        Header(navigation()),
        Main(question(chat.id), cls="page-dropdown"),
        Footer(answer_list(chat.id)),
        #Script(src="/static/minimal-theme-switcher.js"),
        cls="container",
        hx_ext="ws",
        ws_connect="/ws_connect",
        
    )

    # Define the CSS for vertical centering
    css_style = Style("""
    .container {
        display: flex;
        flex-direction: column;
        justify-content: center; /* Centers vertically */
        min-height: 100vh; /* Minimum height of full viewport */
        box-sizing: border-box;
    }
    """)
    return Title("Explore!"), css_style, body

# WebSocket connection bookkeeping
ws_connections = {}

async def on_connect(send):
    ws_connections[send.args[0].client] = send
    print(f"WS    connect: {send.args[0].client}, total open: {len(ws_connections)}")

async def on_disconnect(send):
    global ws_connections
    ws_connections = {
        key: value
        for key, value in ws_connections.items()
        if send.args[0].client_state == WebSocketState.CONNECTED
    }
    print(f"WS disconnect: {send.args[0].client}, total open: {len(ws_connections)}")

@app.ws("/ws_connect", conn=on_connect, disconn=on_disconnect)
async def ws(msg: str, send):
    pass

async def update_chat(model: str, card: Card, chat: Any, cleared_inpput, busy_button):
    inputs = {"messages": [("user", card.question)]}    # question is set as the inputs
    config = {"configurable": {"thread_id": chat.id}}   # configuring the chat history
    try:
        result = get_agent(model).invoke(inputs, config)
        print(f"{model} returned result.")
        if (len(result["messages"]) >= 2) and (
            isinstance(result["messages"][-2], ToolMessage)
        ):
            tmsg = result["messages"][-2]
            card.sources = tmsg.artifact["results"]
            card.images = tmsg.artifact["images"]
        card.content = result["messages"][-1].content
        print(card.content)
        chats.upsert(chat) # Updating or inserting chat object (depending if id already exists)
        success = True
    except BadRequestError as e:
        # e = "some error"
        print(f"Exception while calling LLM: {e}")
        card.content = (
            f"Sorry, due to some technical issue no response could be generated: \n{e}"
        )
        success = False

    card.model_id = model
    card.busy = False
    cleared_inpput.disabled = False
    busy_button.disabled = False
    for send in ws_connections.values():
        try:
            await send(card)
            await send(cleared_inpput)
            await send(busy_button)
            if success:
                await send(question_list())
        except:
            pass
    return success

chat_success = False

@threaded
def generate_chat(model: str, card: Card, chat: Any, cleared_inpput, busy_button):
    chat.title = card.question if chat.title == None else chat.title
    chat.updated = datetime.now()
    success = asyncio.run(update_chat(model, card, chat, cleared_inpput, busy_button))
    if success:
        chat_success = True
        global new_chatDTO
        if chat is new_chatDTO:
            new_chatDTO = ChatDTO()
            new_chatDTO.id = shortuuid.uuid()

@rt("/chat/{id}")
async def post(question: str, id: str):
    try:
        if id == new_chatDTO.id:
            chat = new_chatDTO
        else:
            chat = chats[id]
    except NotFoundError:
        # TODO need to rewrite URL if id != new_ChatDTO.id
        chat = new_chatDTO

    card = ChatCard(question=question, content="", busy=True)
    cleared_inpput = Input(
        id="new-question",
        name="question",
        autofocus=True,
        placeholder="Ask your question here...",
        autocomplete="off",
        disabled=True,
        hx_swap_oob="true",
    )
    busy_button = Button(
        "Answer",
        id="answer-btn",
        cls="hidden-default",
        disabled=True,
        hx_swap_oob="true",
    )

    # call response generation in seperate Thread
    generate_chat(selected_model, card, chat, cleared_inpput, busy_button)

    return card, cleared_inpput, busy_button

def main():
    print("preparing html server")
    serve()

if __name__ == "__main__":
    main()

# IntelliExo: Your Panel of Personal AI Advisors 

IntelliExo is an innovative AI platform that provides personalized advice and insights by simulating conversations with various historical figures, thought leaders, and experts. Using Knowledge Graph RAG technology, each AI advisor maintains the authentic voice, knowledge, and perspective of their real-world counterpart.

## Features

- **Multiple AI Personas**: Interact with various personalities including Lee Kuan Yew, Albert Einstein, Confucius, Daniel Kahneman, and more
- **Knowledge-Based Responses**: Utilizes LightRAG for accurate information retrieval from persona-specific documents
- **Personalised Advice**: Adapts responses based on your profile, e.g. background, personality, goals.
- **Voice Synthesis**: Listen to responses in persona-specific voices using ElevenLabs technology
- **Viewing Knowledge Graph**: Explore the relationships and connections between different personas and their knowledge bases through the **"Knowledge Graph"** page
- **Response Summaries**: Get concise summaries of multiple advisor responses
- **Customizable AI Advisors**: Create and manage your own custom personas through **"Manage Personas"** page and uploading documents like interview transcripts, biographies, and articles


## Technical Stack 

- **Framework**: Streamlit
- **Language Models**: Llama3.1 70B Instruct (via NVIDIA NIMs)
- **Voice Synthesis**: ElevenLabs API
- **Document Processing**: textract
- **Vector Storage**: FAISS
- **Knowledge Base**: LightRAG (Knowledge Graph RAG) implementation
- **Pre-requisites**: Python 3.11.8 and above, Streamlit 1.41.1 and above.

## Project Structure

```
intelliExo/
├── data/                    # Persona-specific knowledge bases
│   ├── Albert Einstein/
│   ├── Lee Kuan Yew/
│   ├── Confucius/
│   ├── Jimmy O Yang/
│   ├── ...
│   ├── persona_profiles.json  # Contains metadata for all personas
│   └── user_profile.json  # Contains information about the user
├── lightrag/               # Custom RAG implementation
├── src/
│   └── pages/             # Streamlit pages
├── main.py                # Main Streamlit application
```

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
NVIDIA_API_KEY=your_nvidia_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

4. Run the application:
```bash
streamlit run main.py
```

## Usage

1. Fill in your user profile information to personalize the experience
1. Select one or more AI advisors from the available personas
1. Ask your question in the chat interface
1. Receive personalized responses from each selected advisor
1. Optionally:
   - Listen to responses in the advisor's voice
   - View source documents for responses
   - Get a summary of all advisors' perspectives
   - Explore the knowledge graph to see connections between entities and their relsationships
   - Create and manage your own personas through the **"Manage Personas"** page

### Creating Custom Personas

1. Navigate to the "Manage Personas" page in the sidebar
1. Click on "Create New Persona"
1. Fill in the required details:
   - Name: A unique name for your persona
   - Persona Prompt: A detailed description of the persona's background, expertise, and perspective
   - Voice ID: Name of voice in your ElevenLabs account
   - Knowledge Base: Upload relevant documents (e.g., interviews, biographies) to enhance the persona's knowledge
1. Click "Create Persona" to save your new custom persona
1. You can start conversing with your custom persona immediately
1. You can add documents to, edit or delete your custom personas at any time from the "Manage Personas" page

## Contributing 🤝
Project By:
Ethan Wei (NVIDIA Student Ambassador), Darren Tan (NVIDIA), Aik Beng Ng (NVIDIA), Simon See (NVIDIA)

An NVAITC APS project (NVIDIA).

## 📄 License

This project is licensed under the MIT License - see the repository's [LICENSE](../../LICENSE) file for details.

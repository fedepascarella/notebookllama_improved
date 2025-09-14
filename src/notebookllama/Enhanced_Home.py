"""
Enhanced NotebookLlama Home Page
Using Docling for document processing and PostgreSQL for storage
"""

import streamlit as st
import io
import os
import asyncio
import tempfile as temp
from dotenv import load_dotenv
import sys
import time
import randomname
import streamlit.components.v1 as components
from pathlib import Path
from typing import Tuple

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import enhanced modules
from enhanced_workflow import WF, FileInputEvent, NotebookOutputEvent
from postgres_manager import DOCUMENT_MANAGER, EnhancedDocument
from audio import PODCAST_GEN, PodcastConfig
from instrumentation import OtelTracesSqlEngine
from llama_index.observability.otel import LlamaIndexOpenTelemetry
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

load_dotenv()

# Initialize instrumentation
span_exporter = OTLPSpanExporter("http://localhost:4318/v1/traces")
instrumentor = LlamaIndexOpenTelemetry(
    service_name_or_resource="enhanced.agent.traces",
    span_exporter=span_exporter,
    debug=True,
)

# Initialize SQL engine for tracing
engine_url = f"postgresql+psycopg2://{os.getenv('pgql_user')}:{os.getenv('pgql_psw')}@localhost:5432/{os.getenv('pgql_db')}"
sql_engine = OtelTracesSqlEngine(
    engine_url=engine_url,
    table_name="enhanced_agent_traces",
    service_name="enhanced.agent.traces",
)


def read_html_file(file_path: str) -> str:
    """Read HTML file content"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


async def run_enhanced_workflow(
    file: io.BytesIO, 
    document_title: str
) -> Tuple[str, str, str, str, str]:
    """
    Run the enhanced workflow using Docling processing
    """
    # Create temp file with proper handling
    with temp.NamedTemporaryFile(suffix=".pdf", delete=False) as fl:
        content = file.getvalue()
        fl.write(content)
        fl.flush()
        temp_path = fl.name

    try:
        st_time = int(time.time() * 1000000)
        
        # Run enhanced workflow
        ev = FileInputEvent(file=temp_path)
        result: NotebookOutputEvent = await WF.run(start_event=ev)

        # Format Q&A
        q_and_a = ""
        for q, a in zip(result.questions, result.answers):
            q_and_a += f"**{q}**\n\n{a}\n\n"
        
        # Format bullet points
        bullet_points = "## Key Highlights\n\n- " + "\n- ".join(result.highlights)

        # Handle mind map
        mind_map = result.mind_map
        if Path(mind_map).is_file():
            mind_map = read_html_file(mind_map)
            try:
                os.remove(result.mind_map)
            except OSError:
                pass

        # Log processing time
        end_time = int(time.time() * 1000000)
        try:
            sql_engine.to_sql_database(start_time=st_time, end_time=end_time)
        except Exception as e:
            print(f"Warning: Could not log to SQL database: {e}")

        # Store in enhanced document manager
        try:
            enhanced_doc = EnhancedDocument(
                id=f"doc_{int(time.time())}",
                document_name=document_title,
                content=result.md_content,
                summary=result.summary,
                q_and_a=q_and_a,
                mindmap=mind_map,
                bullet_points=bullet_points,
                metadata={
                    "processed_by": "enhanced_workflow",
                    "processing_time_ms": end_time - st_time,
                    "questions_count": len(result.questions),
                    "highlights_count": len(result.highlights),
                },
                is_processed=True
            )
            
            await DOCUMENT_MANAGER.put_document(enhanced_doc)
            
        except Exception as e:
            print(f"Warning: Could not store document: {e}")

        return result.md_content, result.summary, q_and_a, bullet_points, mind_map

    finally:
        try:
            os.remove(temp_path)
        except OSError:
            await asyncio.sleep(0.1)
            try:
                os.remove(temp_path)
            except OSError:
                pass


def sync_run_enhanced_workflow(file: io.BytesIO, document_title: str):
    """Synchronous wrapper for the enhanced workflow"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    run_enhanced_workflow(file, document_title)
                )
                return future.result()
        else:
            return loop.run_until_complete(
                run_enhanced_workflow(file, document_title)
            )
    except RuntimeError:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        return asyncio.run(run_enhanced_workflow(file, document_title))


async def create_podcast(file_content: str, config: PodcastConfig = None):
    """Create podcast using the existing audio module"""
    if PODCAST_GEN is None:
        raise Exception("Podcast generation not available. Check your API keys.")
    
    audio_fl = await PODCAST_GEN.create_conversation(
        file_transcript=file_content, 
        config=config
    )
    return audio_fl


def sync_create_podcast(file_content: str, config: PodcastConfig = None):
    """Synchronous wrapper for podcast creation"""
    return asyncio.run(create_podcast(file_content=file_content, config=config))


# Streamlit Page Configuration
st.set_page_config(
    page_title="NotebookLlama Enhanced - Home",
    page_icon="🦙",
    layout="wide",
    menu_items={
        "Get Help": "https://github.com/run-llama/notebooklm-clone/discussions/categories/general",
        "Report a bug": "https://github.com/run-llama/notebooklm-clone/issues/",
        "About": "Enhanced NotebookLM alternative powered by Docling and PostgreSQL!",
    },
)

st.sidebar.header("🦙 Enhanced Home")
st.sidebar.info("Enhanced with Docling processing and PostgreSQL storage!")

# Show enhancement notice
st.sidebar.markdown("---")
st.sidebar.markdown("### ✨ **What's New**")
st.sidebar.success("🔥 **Docling Processing**: Advanced PDF parsing with AI models")
st.sidebar.success("🐘 **PostgreSQL Storage**: Vector search and enhanced querying")
st.sidebar.success("🔗 **Custom Chat API**: Connect to external AI services")

st.markdown("---")
st.markdown("## 🦙 NotebookLlama Enhanced - Home")

# Initialize session state
if "enhanced_workflow_results" not in st.session_state:
    st.session_state.enhanced_workflow_results = None
if "document_title" not in st.session_state:
    st.session_state.document_title = randomname.get_name(
        adj=("technology", "modern", "advanced"), 
        noun=("documents", "research", "analysis")
    )

# Document title input
document_title = st.text_input(
    label="📄 Document Title",
    value=st.session_state.document_title,
    key="enhanced_document_title_input",
    help="Give your document a descriptive name"
)

# Update session state when the input changes
if document_title != st.session_state.document_title:
    st.session_state.document_title = document_title

# File uploader with enhanced description
st.markdown("### 📤 Upload Document")
st.markdown("Upload your PDF file for enhanced processing with **Docling AI models**")

file_input = st.file_uploader(
    label="Choose a PDF file",
    accept_multiple_files=False,
    type=['pdf'],
    help="Supported: PDF files. Docling provides advanced parsing with table extraction, layout analysis, and OCR."
)

if file_input is not None:
    # Document processing section
    st.markdown("### 🔄 Document Processing")
    
    # Process Document Button
    if st.button("🚀 Process Document with Docling", type="primary"):
        with st.spinner("🤖 Processing with Docling AI models... This may take a few minutes."):
            try:
                md_content, summary, q_and_a, bullet_points, mind_map = (
                    sync_run_enhanced_workflow(file_input, st.session_state.document_title)
                )
                
                st.session_state.enhanced_workflow_results = {
                    "md_content": md_content,
                    "summary": summary,
                    "q_and_a": q_and_a,
                    "bullet_points": bullet_points,
                    "mind_map": mind_map,
                }
                
                st.success("✅ Document processed successfully with enhanced capabilities!")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                st.markdown("**Troubleshooting:**")
                st.markdown("- Ensure the PDF is not corrupted")
                st.markdown("- Check if PostgreSQL is running")
                st.markdown("- Verify OpenAI API key is set")

    # Display results if available
    if st.session_state.enhanced_workflow_results:
        results = st.session_state.enhanced_workflow_results

        # Create tabs for better organization
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🎯 Highlights", "❓ FAQ", "🗺️ Mind Map"])
        
        with tab1:
            st.markdown("## 📋 Document Summary")
            st.markdown(results["summary"])
            
            # Add metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Content Length", f"{len(results['md_content']):,} chars")
            with col2:
                st.metric("📝 Summary Length", f"{len(results['summary'])} chars")
            with col3:
                if results["q_and_a"]:
                    qa_count = results["q_and_a"].count("**")
                    st.metric("❓ Q&A Pairs", qa_count // 2)

        with tab2:
            st.markdown("## 🎯 Key Highlights")
            st.markdown(results["bullet_points"])

        with tab3:
            st.markdown("## ❓ Frequently Asked Questions")
            if results["q_and_a"]:
                st.markdown(results["q_and_a"])
            else:
                st.info("No Q&A content generated")

        with tab4:
            st.markdown("## 🗺️ Mind Map")
            if results["mind_map"] and results["mind_map"] != "❌ Mind map generation failed":
                try:
                    components.html(results["mind_map"], height=800, scrolling=True)
                except Exception as e:
                    st.error(f"Error displaying mind map: {e}")
                    st.code(results["mind_map"][:1000] + "..." if len(results["mind_map"]) > 1000 else results["mind_map"])
            else:
                st.warning("Mind map could not be generated")

        # Podcast Generation Section
        st.markdown("---")
        st.markdown("## 🎙️ Generate AI Podcast")

        with st.expander("🎛️ Podcast Configuration", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                style = st.selectbox(
                    "🎨 Conversation Style",
                    ["conversational", "interview", "debate", "educational"],
                    help="The overall style of the podcast conversation",
                )

                tone = st.selectbox(
                    "🎵 Tone",
                    ["friendly", "professional", "casual", "energetic"],
                    help="The tone of voice for the conversation",
                )

                target_audience = st.selectbox(
                    "👥 Target Audience",
                    ["general", "technical", "business", "expert", "beginner"],
                    help="Who is the intended audience for this podcast?",
                )

            with col2:
                speaker1_role = st.text_input(
                    "🎤 Speaker 1 Role",
                    value="host",
                    help="The role or persona of the first speaker",
                )

                speaker2_role = st.text_input(
                    "🎤 Speaker 2 Role",
                    value="expert guest",
                    help="The role or persona of the second speaker",
                )

            # Focus Topics
            st.markdown("**🎯 Focus Topics** (optional)")
            focus_topics_input = st.text_area(
                "Enter topics to emphasize (one per line)",
                help="List specific topics you want the podcast to focus on",
                placeholder="Key technical innovations\nPractical applications\nFuture implications",
            )

            # Parse focus topics
            focus_topics = None
            if focus_topics_input.strip():
                focus_topics = [
                    topic.strip()
                    for topic in focus_topics_input.split("\n")
                    if topic.strip()
                ]

            # Custom Prompt
            custom_prompt = st.text_area(
                "✍️ Custom Instructions (optional)",
                help="Add any additional instructions for the podcast generation",
                placeholder="Focus on practical examples and avoid too much technical jargon...",
            )

            # Create config object
            podcast_config = PodcastConfig(
                style=style,
                tone=tone,
                focus_topics=focus_topics,
                target_audience=target_audience,
                custom_prompt=custom_prompt if custom_prompt.strip() else None,
                speaker1_role=speaker1_role,
                speaker2_role=speaker2_role,
            )

        # Generate Podcast Button
        if st.button("🎙️ Generate AI Podcast", type="secondary"):
            if not results["md_content"]:
                st.error("No content available for podcast generation")
            else:
                with st.spinner("🎵 Generating podcast conversation... This may take several minutes."):
                    try:
                        audio_file = sync_create_podcast(
                            results["md_content"], 
                            config=podcast_config
                        )
                        
                        st.success("🎉 Podcast generated successfully!")

                        # Display audio player
                        st.markdown("### 🔊 Your AI-Generated Podcast")
                        if os.path.exists(audio_file):
                            with open(audio_file, "rb") as f:
                                audio_bytes = f.read()
                            os.remove(audio_file)
                            
                            st.audio(audio_bytes, format="audio/mp3")
                            
                            # Download button
                            st.download_button(
                                label="⬇️ Download Podcast",
                                data=audio_bytes,
                                file_name=f"podcast_{st.session_state.document_title.replace(' ', '_')}.mp3",
                                mime="audio/mp3"
                            )
                        else:
                            st.error("Audio file not found.")

                    except Exception as e:
                        st.error(f"❌ Error generating podcast: {str(e)}")
                        if "ELEVENLABS_API_KEY" not in os.environ:
                            st.warning("💡 Make sure you have set your ELEVENLABS_API_KEY environment variable")

else:
    # Welcome message when no file is uploaded
    st.markdown("### 👋 Welcome to Enhanced NotebookLlama!")
    
    st.markdown("""
    🚀 **What's New in the Enhanced Version:**
    
    ✨ **Docling AI Processing**: Advanced document parsing with state-of-the-art AI models
    - 📊 Superior table extraction and structure recognition
    - 🎯 Advanced layout analysis and reading order detection
    - 🔍 Intelligent OCR for scanned documents
    - 🎨 Image classification and processing
    
    🐘 **PostgreSQL Integration**: 
    - 🔎 Vector-based semantic search
    - 💾 Enhanced document storage with metadata
    - 📈 Better query performance and scalability
    
    🔗 **Custom Chat API**: Connect to any AI service
    - 🌐 Support for OpenAI, Anthropic, and custom APIs
    - 🛠️ Configurable message formats and authentication
    - 💬 Real-time chat interface
    
    📤 **To get started**: Upload a PDF file above!
    """)
    
    # Features showcase
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 🤖 AI-Powered Processing
        - Advanced PDF parsing
        - Table & image extraction
        - Smart content analysis
        """)
    
    with col2:
        st.markdown("""
        #### 🎙️ Podcast Generation  
        - AI-generated conversations
        - Customizable voices & styles
        - Multiple export formats
        """)
    
    with col3:
        st.markdown("""
        #### 🔍 Smart Search
        - Vector-based similarity
        - Semantic understanding
        - Fast query responses
        """)

# Footer
st.markdown("---")
st.markdown("### 🔧 System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Check Docling
    try:
        from docling_processor import DOCLING_PROCESSOR
        st.success("✅ Docling Ready")
    except Exception:
        st.error("❌ Docling Error")

with col2:
    # Check PostgreSQL
    try:
        DOCUMENT_MANAGER.get_session().close()
        st.success("✅ PostgreSQL Connected")
    except Exception:
        st.error("❌ PostgreSQL Error")

with col3:
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        st.success("✅ OpenAI Configured")
    else:
        st.warning("⚠️ OpenAI Not Set")

with col4:
    # Check ElevenLabs
    if PODCAST_GEN is not None:
        st.success("✅ Audio Ready")
    else:
        st.warning("⚠️ Audio Not Available")

if __name__ == "__main__":
    instrumentor.start_registering()

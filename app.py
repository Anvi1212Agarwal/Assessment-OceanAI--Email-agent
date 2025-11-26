"""
Email Productivity Agent - Main Streamlit Application
A prompt-driven email agent using Google Gemini AI
"""
import streamlit as st
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import custom modules with error handling
try:
    from src.storage import Storage
    from src.llm_handler import LLMHandler
    from src.email_processor import EmailProcessor
    from src.prompt_manager import PromptManager
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Please make sure all files are in the correct directories:")
    st.code("""
    src/
    ├── __init__.py (can be empty)
    ├── storage.py
    ├── llm_handler.py
    ├── email_processor.py
    └── prompt_manager.py
    """)
    st.stop()

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Email Productivity Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .email-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .category-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 5px;
    }
    .important { background-color: #ff6b6b; color: white; }
    .newsletter { background-color: #4ecdc4; color: white; }
    .spam { background-color: #95a5a6; color: white; }
    .to-do { background-color: #ffd93d; color: black; }
    .update { background-color: #6c5ce7; color: white; }
    .stTextArea textarea {
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.storage = Storage()
        st.session_state.selected_email = None
        st.session_state.current_tab = "Inbox"
        st.session_state.chat_history = []
        st.session_state.processing_complete = False
        st.session_state.api_key_set = False
        
        # Try to initialize LLM
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                st.session_state.llm = LLMHandler(api_key)
                st.session_state.prompt_manager = PromptManager(st.session_state.storage)
                st.session_state.email_processor = EmailProcessor(
                    st.session_state.llm, 
                    st.session_state.storage
                )
                st.session_state.api_key_set = True
            except Exception as e:
                st.session_state.api_key_set = False
                st.session_state.api_error = str(e)

initialize_session_state()

# Main title
st.title("📧 Email Productivity Agent")
st.markdown("*Powered by Google Gemini AI*")

# Sidebar for API Key and Navigation
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Input
    if not st.session_state.api_key_set:
        st.warning("⚠️ Please enter your Gemini API Key")
        api_key_input = st.text_input(
            "Gemini API Key", 
            type="password",
            help="Get your API key from https://makersuite.google.com/app/apikey"
        )
        
        if st.button("Set API Key", type="primary"):
            if api_key_input:
                try:
                    st.session_state.llm = LLMHandler(api_key_input)
                    st.session_state.prompt_manager = PromptManager(st.session_state.storage)
                    st.session_state.email_processor = EmailProcessor(
                        st.session_state.llm,
                        st.session_state.storage
                    )
                    st.session_state.api_key_set = True
                    st.success("✅ API Key set successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("Please enter an API key")
    else:
        st.success("✅ API Key configured")
        if st.button("Change API Key"):
            st.session_state.api_key_set = False
            st.rerun()
    
    st.divider()
    
    # Navigation
    st.header("🧭 Navigation")
    nav_option = st.radio(
        "Select View",
        ["📥 Inbox Viewer", "🧠 Prompt Manager", "💬 Email Agent Chat", "✉️ Draft Manager"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Quick Stats
    if st.session_state.api_key_set:
        st.header("📊 Quick Stats")
        emails = st.session_state.storage.load_inbox()
        processed = st.session_state.storage.load_processed_emails()
        drafts = st.session_state.storage.load_drafts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Emails", len(emails))
            st.metric("Drafts", len(drafts))
        with col2:
            st.metric("Processed", len(processed))
            action_items = st.session_state.email_processor.get_all_action_items()
            st.metric("Action Items", len(action_items))

# Main content area
if not st.session_state.api_key_set:
    st.info("👈 Please set your Gemini API Key in the sidebar to get started")
    st.markdown("""
    ### Getting Started
    
    1. **Get API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. **Enter Key**: Paste your API key in the sidebar
    3. **Start Using**: Process emails, chat with the agent, and manage drafts!
    
    ### Features
    - 📧 **Email Categorization**: Automatically sort emails into categories
    - ✅ **Action Items**: Extract tasks and deadlines
    - 🤖 **Auto-Reply**: Generate draft responses
    - 💬 **Chat Interface**: Ask questions about your emails
    - 🧠 **Custom Prompts**: Customize AI behavior
    """)

elif nav_option == "📥 Inbox Viewer":
    st.header("📥 Inbox Viewer")
    
    # Load and Process Emails button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("🔄 Process All Emails", type="primary", use_container_width=True):
            with st.spinner("Processing emails..."):
                emails = st.session_state.storage.load_inbox()
                prompts = st.session_state.prompt_manager.get_all_prompts()
                
                progress_bar = st.progress(0)
                for i, email in enumerate(emails):
                    st.session_state.email_processor.process_single_email(email, prompts)
                    progress_bar.progress((i + 1) / len(emails))
                
                st.session_state.processing_complete = True
                st.success(f"✅ Processed {len(emails)} emails!")
                st.rerun()
    
    with col2:
        if st.button("📤 Load Mock Inbox", use_container_width=True):
            st.info("Mock inbox already loaded from data/mock_inbox.json")
    
    with col3:
        if st.button("🗑️ Clear Processed", use_container_width=True):
            st.session_state.storage.save_json(
                st.session_state.storage.processed_file, 
                {}
            )
            st.success("Cleared processed data")
            st.rerun()
    
    # Filter options
    st.subheader("🔍 Filter Emails")
    col1, col2 = st.columns(2)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "Important", "Newsletter", "Spam", "To-Do", "Update"]
        )
    
    with col2:
        search_term = st.text_input("🔎 Search", placeholder="Search subject or sender...")
    
    # Display emails
    emails = st.session_state.storage.load_inbox()
    processed_emails = st.session_state.storage.load_processed_emails()
    
    # Apply filters
    filtered_emails = emails
    if category_filter != "All":
        filtered_emails = [
            e for e in emails 
            if processed_emails.get(e['id'], {}).get('category') == category_filter
        ]
    
    if search_term:
        filtered_emails = [
            e for e in filtered_emails
            if search_term.lower() in e.get('subject', '').lower() or
               search_term.lower() in e.get('sender', '').lower()
        ]
    
    st.markdown(f"**Showing {len(filtered_emails)} emails**")
    
    # Display each email
    for email in filtered_emails:
        email_id = email.get('id')
        processed = processed_emails.get(email_id, {})
        category = processed.get('category', 'Unprocessed')
        
        with st.expander(f"📧 **{email.get('subject')}** - From: {email.get('sender')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Category badge
                category_class = category.lower().replace('-', '')
                st.markdown(
                    f'<span class="category-badge {category_class}">{category}</span>',
                    unsafe_allow_html=True
                )
                
                st.caption(f"📅 {email.get('timestamp', 'No date')}")
                st.markdown("**Email Body:**")
                st.text(email.get('body', 'No content'))
                
                # Summary
                if processed.get('summary'):
                    st.markdown("**📝 Summary:**")
                    st.info(processed['summary'])
                
                # Action items
                action_items = processed.get('action_items', {}).get('tasks', [])
                if action_items:
                    st.markdown("**✅ Action Items:**")
                    for task in action_items:
                        priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(task.get('priority', 'Low'), "⚪")
                        st.markdown(f"{priority_emoji} **{task.get('task')}**")
                        st.caption(f"Deadline: {task.get('deadline', 'Not specified')}")
                
                # Suggested reply
                if processed.get('suggested_reply'):
                    st.markdown("**💬 Suggested Reply:**")
                    reply = processed['suggested_reply']
                    st.code(f"Subject: {reply.get('subject', '')}\n\n{reply.get('body', '')}")
            
            with col2:
                if st.button("💬 Chat", key=f"chat_{email_id}"):
                    st.session_state.selected_email = email_id
                    st.session_state.current_tab = "Email Agent Chat"
                    st.rerun()
                
                if st.button("✉️ Draft Reply", key=f"draft_{email_id}"):
                    if processed.get('suggested_reply'):
                        draft = {
                            'id': f"draft_{email_id}",
                            'to': email.get('sender'),
                            'subject': processed['suggested_reply'].get('subject'),
                            'body': processed['suggested_reply'].get('body'),
                            'reply_to': email_id,
                            'created_at': datetime.now().isoformat()
                        }
                        st.session_state.storage.save_draft(draft)
                        st.success("Draft saved!")
                
                if st.button("🔄 Reprocess", key=f"reprocess_{email_id}"):
                    with st.spinner("Reprocessing..."):
                        prompts = st.session_state.prompt_manager.get_all_prompts()
                        st.session_state.email_processor.reprocess_email(email_id, prompts)
                    st.success("Reprocessed!")
                    st.rerun()

elif nav_option == "🧠 Prompt Manager":
    st.header("🧠 Prompt Manager")
    
    st.markdown("""
    Customize how the AI agent processes your emails by editing the prompts below.
    Changes will apply to newly processed emails.
    """)
    
    # Load current prompts
    prompts = st.session_state.prompt_manager.get_all_prompts()
    
    # Tabs for different prompts
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 Categorization", 
        "✅ Action Items", 
        "✉️ Auto-Reply", 
        "📝 Summary"
    ])
    
    with tab1:
        st.subheader("Email Categorization Prompt")
        st.caption("This prompt determines how emails are categorized")
        
        categorization_prompt = st.text_area(
            "Categorization Prompt",
            value=prompts.get('categorization', ''),
            height=300,
            key="cat_prompt"
        )
        
        if st.button("💾 Save Categorization Prompt", type="primary"):
            st.session_state.prompt_manager.update_prompt('categorization', categorization_prompt)
            st.success("✅ Categorization prompt saved!")
    
    with tab2:
        st.subheader("Action Item Extraction Prompt")
        st.caption("This prompt extracts tasks and deadlines from emails")
        
        action_prompt = st.text_area(
            "Action Item Prompt",
            value=prompts.get('action_item', ''),
            height=300,
            key="action_prompt"
        )
        
        if st.button("💾 Save Action Item Prompt", type="primary"):
            st.session_state.prompt_manager.update_prompt('action_item', action_prompt)
            st.success("✅ Action item prompt saved!")
    
    with tab3:
        st.subheader("Auto-Reply Generation Prompt")
        st.caption("This prompt generates draft replies to emails")
        
        reply_prompt = st.text_area(
            "Auto-Reply Prompt",
            value=prompts.get('auto_reply', ''),
            height=300,
            key="reply_prompt"
        )
        
        if st.button("💾 Save Auto-Reply Prompt", type="primary"):
            st.session_state.prompt_manager.update_prompt('auto_reply', reply_prompt)
            st.success("✅ Auto-reply prompt saved!")
    
    with tab4:
        st.subheader("Email Summary Prompt")
        st.caption("This prompt creates concise email summaries")
        
        summary_prompt = st.text_area(
            "Summary Prompt",
            value=prompts.get('summary', ''),
            height=300,
            key="summary_prompt"
        )
        
        if st.button("💾 Save Summary Prompt", type="primary"):
            st.session_state.prompt_manager.update_prompt('summary', summary_prompt)
            st.success("✅ Summary prompt saved!")
    
    st.divider()
    
    # Reset to defaults
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Reset All to Defaults", type="secondary"):
            st.session_state.prompt_manager.reset_to_defaults()
            st.success("✅ All prompts reset to defaults!")
            st.rerun()

elif nav_option == "💬 Email Agent Chat":
    st.header("💬 Email Agent Chat")
    
    st.markdown("Ask questions about your emails or request actions")
    
    # Email selector
    emails = st.session_state.storage.load_inbox()
    email_options = ["General Questions"] + [
        f"{e.get('subject')} - {e.get('sender')}" 
        for e in emails
    ]
    
    selected_email_display = st.selectbox(
        "Select Email Context (optional)",
        email_options,
        index=0 if not st.session_state.selected_email else None
    )
    
    # Get selected email ID
    selected_email_id = None
    if selected_email_display != "General Questions":
        selected_index = email_options.index(selected_email_display) - 1
        selected_email_id = emails[selected_index].get('id')
    
    # Chat interface
    st.subheader("Chat History")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Agent:** {message['content']}")
            st.divider()
    
    # Chat input
    user_query = st.text_input("Ask a question or request an action:", key="chat_input")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("Send 📤", type="primary", use_container_width=True):
            if user_query:
                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_query
                })
                
                # Prepare context
                context = {}
                if selected_email_id:
                    context['email'] = st.session_state.storage.get_email_by_id(selected_email_id)
                    context['processed_data'] = st.session_state.storage.get_processed_email(selected_email_id)
                
                # Get response from LLM
                with st.spinner("Thinking..."):
                    response = st.session_state.llm.chat_with_context(user_query, context)
                
                # Add agent response to history
                st.session_state.chat_history.append({
                    'role': 'agent',
                    'content': response
                })
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat 🗑️", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    # Quick action buttons
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Show All Tasks"):
            action_items = st.session_state.email_processor.get_all_action_items()
            if action_items:
                st.markdown("### All Action Items")
                for item in action_items:
                    st.markdown(f"- **{item.get('task')}** (from: {item.get('email_subject')})")
                    st.caption(f"Deadline: {item.get('deadline')} | Priority: {item.get('priority')}")
            else:
                st.info("No action items found")
    
    with col2:
        if st.button("🔴 Show Important"):
            important = st.session_state.email_processor.get_emails_by_category('Important')
            if important:
                st.markdown(f"### {len(important)} Important Emails")
                for email in important:
                    st.markdown(f"- **{email.get('subject')}** from {email.get('sender')}")
            else:
                st.info("No important emails")
    
    with col3:
        if st.button("📋 Show To-Do"):
            todos = st.session_state.email_processor.get_emails_by_category('To-Do')
            if todos:
                st.markdown(f"### {len(todos)} To-Do Emails")
                for email in todos:
                    st.markdown(f"- **{email.get('subject')}** from {email.get('sender')}")
            else:
                st.info("No to-do emails")

elif nav_option == "✉️ Draft Manager":
    st.header("✉️ Draft Manager")
    
    # Load drafts
    drafts = st.session_state.storage.load_drafts()
    
    st.markdown(f"**{len(drafts)} draft(s) saved**")
    
    # Create new draft
    with st.expander("➕ Create New Draft", expanded=False):
        new_to = st.text_input("To:", key="new_to")
        new_subject = st.text_input("Subject:", key="new_subject")
        new_body = st.text_area("Body:", height=200, key="new_body")
        
        if st.button("💾 Save Draft", type="primary"):
            if new_to and new_subject and new_body:
                draft = {
                    'to': new_to,
                    'subject': new_subject,
                    'body': new_body,
                    'created_at': datetime.now().isoformat()
                }
                st.session_state.storage.save_draft(draft)
                st.success("✅ Draft saved!")
                st.rerun()
            else:
                st.error("Please fill in all fields")
    
    st.divider()
    
    # Display existing drafts
    if drafts:
        for draft in drafts:
            with st.expander(f"✉️ {draft.get('subject', 'No subject')} → {draft.get('to', 'Unknown')}"):
                st.markdown(f"**To:** {draft.get('to', 'Unknown')}")
                st.markdown(f"**Subject:** {draft.get('subject', 'No subject')}")
                st.markdown(f"**Created:** {draft.get('created_at', 'Unknown')}")
                
                if draft.get('reply_to'):
                    st.caption(f"↩️ Reply to email: {draft.get('reply_to')}")
                
                st.markdown("**Body:**")
                edited_body = st.text_area(
                    "Edit draft:", 
                    value=draft.get('body', ''),
                    height=200,
                    key=f"edit_{draft.get('id')}"
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("💾 Update", key=f"update_{draft.get('id')}"):
                        draft['body'] = edited_body
                        st.session_state.storage.save_draft(draft)
                        st.success("Draft updated!")
                
                with col2:
                    st.info("⚠️ Drafts are not sent automatically")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{draft.get('id')}"):
                        st.session_state.storage.delete_draft(draft.get('id'))
                        st.success("Draft deleted!")
                        st.rerun()
    else:
        st.info("No drafts yet. Process emails or create a new draft above!")

# Footer
st.divider()
st.caption("Email Productivity Agent | Powered by Google Gemini AI | Made with ❤️ using Streamlit")










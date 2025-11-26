"""
Prompt Manager - handles prompt CRUD operations
"""
from typing import Dict
from .storage import Storage


class PromptManager:
    """Manages prompt templates"""
    
    def __init__(self, storage: Storage):
        self.storage = storage
        
        # Default prompts if none exist
        self.default_prompts = {
            "categorization": "Analyze the email and categorize it into exactly ONE of these categories: Important, Newsletter, Spam, To-Do, or Update.\n\nCategorization rules:\n- **Important**: Urgent matters, critical security issues, deadline-driven tasks, executive communications\n- **Newsletter**: Marketing emails, promotional content, news digests, automated updates from services\n- **Spam**: Suspicious emails, lottery/prize scams, unsolicited offers, obvious phishing attempts\n- **To-Do**: Direct requests requiring user action, meeting requests needing response, approval requests, review requests\n- **Update**: Status updates, FYI emails, project progress reports, informational messages\n\nRespond with ONLY the category name, nothing else.",
            
            "action_item": "Extract all action items and tasks from this email. For each action item, identify:\n1. The specific task or action required\n2. Any deadline or due date mentioned\n3. Priority level (High/Medium/Low)\n\nRespond in JSON format:\n{\n  \"tasks\": [\n    {\n      \"task\": \"description of the task\",\n      \"deadline\": \"date or 'Not specified'\",\n      \"priority\": \"High/Medium/Low\"\n    }\n  ]\n}\n\nIf no action items exist, return: {\"tasks\": []}",
            
            "auto_reply": "Generate a professional email reply based on the email content and context.\n\nGuidelines:\n1. If it's a meeting request: Acknowledge and ask for an agenda or confirm availability\n2. If it's a task request: Confirm receipt and provide estimated timeline\n3. If it's informational: Acknowledge and thank the sender\n4. Keep the tone professional but friendly\n5. Keep replies concise (3-5 sentences)\n\nProvide the reply in this JSON format:\n{\n  \"subject\": \"Re: [original subject]\",\n  \"body\": \"your reply here\"\n}",
            
            "summary": "Provide a concise 2-3 sentence summary of this email highlighting:\n1. Main purpose/topic\n2. Key information or requests\n3. Any deadlines or important dates\n\nKeep it brief and actionable."
        }
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompt templates"""
        prompts = self.storage.load_prompts()
        
        # If no prompts exist, initialize with defaults
        if not prompts:
            self.storage.save_prompts(self.default_prompts)
            return self.default_prompts.copy()
        
        return prompts
    
    def get_prompt(self, prompt_type: str) -> str:
        """Get a specific prompt by type"""
        prompts = self.get_all_prompts()
        return prompts.get(prompt_type, "")
    
    def update_prompt(self, prompt_type: str, prompt_text: str) -> bool:
        """Update a specific prompt"""
        return self.storage.update_prompt(prompt_type, prompt_text)
    
    def save_all_prompts(self, prompts: Dict[str, str]) -> bool:
        """Save all prompts"""
        return self.storage.save_prompts(prompts)
    
    def reset_to_defaults(self) -> bool:
        """Reset all prompts to default values"""
        return self.storage.save_prompts(self.default_prompts)
    
    def get_prompt_types(self) -> list:
        """Get list of available prompt types"""
        return list(self.default_prompts.keys())
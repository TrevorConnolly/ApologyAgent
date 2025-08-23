from agents import function_tool
from typing import Dict, List, Optional

@function_tool
def craft_personalized_message(situation: str, recipient_name: str, relationship_type: str, 
                              tone: str = "sincere", length: str = "medium") -> Dict[str, str]:
    """
    Craft a personalized apology message based on the situation and relationship.
    """
    
    message_templates = {
        "romantic": {
            "sincere": {
                "opening": f"My dearest {recipient_name},",
                "acknowledgment": "I know I hurt you, and I can't express how sorry I am.",
                "responsibility": "What I did was wrong, and there's no excuse for it.",
                "impact": "I see the pain in your eyes, and knowing I caused it breaks my heart.",
                "commitment": "I'm committed to doing whatever it takes to rebuild your trust.",
                "closing": "You mean everything to me, and I hope you can find it in your heart to forgive me."
            },
            "heartfelt": {
                "opening": f"Dear {recipient_name},",
                "acknowledgment": "I've been thinking about what happened, and I realize how much I've hurt you.",
                "responsibility": "I take full responsibility for my actions and the pain they caused.",
                "impact": "Your feelings matter more to me than anything, and I failed to honor that.",
                "commitment": "I promise to work on myself and be the partner you deserve.",
                "closing": "I love you deeply and hope we can work through this together."
            }
        },
        "friend": {
            "sincere": {
                "opening": f"Hey {recipient_name},",
                "acknowledgment": "I've been thinking about what happened between us, and I know I messed up.",
                "responsibility": "What I did was selfish and inconsiderate, and I own that completely.",
                "impact": "I value our friendship so much, and I hate that my actions put it at risk.",
                "commitment": "I want to make this right and prove that I can be a better friend.",
                "closing": "You mean a lot to me, and I hope we can move forward together."
            },
            "casual": {
                "opening": f"Hi {recipient_name},",
                "acknowledgment": "I know things got weird between us, and that's on me.",
                "responsibility": "I handled the situation poorly and I'm sorry for that.",
                "impact": "Your friendship is important to me, and I don't want to lose it over this.",
                "commitment": "I'll do better next time - you have my word on that.",
                "closing": "Hope we can put this behind us and get back to normal."
            }
        },
        "family": {
            "sincere": {
                "opening": f"Dear {recipient_name},",
                "acknowledgment": "I know I disappointed you, and that weighs heavily on my heart.",
                "responsibility": "I made a poor choice, and I understand why you're upset with me.",
                "impact": "Family means everything to me, and knowing I've caused you pain is awful.",
                "commitment": "I want to learn from this and be someone you can be proud of again.",
                "closing": "I love you and hope you can forgive me in time."
            },
            "respectful": {
                "opening": f"Dear {recipient_name},",
                "acknowledgment": "I realize that my actions have hurt you and disappointed our family.",
                "responsibility": "I accept full responsibility for what happened and its consequences.",
                "impact": "I understand that I've damaged the trust between us.",
                "commitment": "I'm committed to making amends and proving myself worthy of your forgiveness.",
                "closing": "Please know that I respect you deeply and hope for your understanding."
            }
        },
        "colleague": {
            "professional": {
                "opening": f"Dear {recipient_name},",
                "acknowledgment": "I want to address what happened and apologize for my actions.",
                "responsibility": "I recognize that my behavior was unprofessional and inappropriate.",
                "impact": "I understand this may have affected our working relationship and team dynamics.",
                "commitment": "I'm committed to maintaining professional standards moving forward.",
                "closing": "I appreciate your professionalism and hope we can continue working together effectively."
            }
        }
    }
    
    # Get appropriate template
    rel_templates = message_templates.get(relationship_type, message_templates["friend"])
    template = rel_templates.get(tone, list(rel_templates.values())[0])
    
    # Construct message based on length
    if length == "short":
        message_parts = [
            template["opening"],
            template["acknowledgment"], 
            template["responsibility"],
            template["closing"]
        ]
    elif length == "long":
        message_parts = [
            template["opening"],
            template["acknowledgment"],
            template["responsibility"], 
            template["impact"],
            template["commitment"],
            "I know words alone aren't enough, but I want you to know that I'm truly sorry.",
            template["closing"],
            "With love and regret," if relationship_type in ["romantic", "family"] else "Sincerely,"
        ]
    else:  # medium
        message_parts = [
            template["opening"],
            template["acknowledgment"],
            template["responsibility"],
            template["impact"],
            template["commitment"],
            template["closing"]
        ]
    
    full_message = "\n\n".join(message_parts)
    
    return {
        "message": full_message,
        "tone_analysis": f"This message strikes a {tone} tone appropriate for {relationship_type} relationships",
        "key_elements": [
            "Takes full responsibility",
            "Acknowledges specific harm caused", 
            "Shows commitment to change",
            "Expresses genuine remorse",
            "Leaves door open for reconciliation"
        ],
        "delivery_recommendations": [
            "Deliver in person if possible for maximum sincerity",
            "If written, use handwriting rather than typed text",
            "Allow them time and space to process after delivery",
            "Be prepared to answer questions or provide clarification"
        ]
    }

@function_tool
def get_apology_message_guidelines(relationship_type: str, severity: int) -> Dict[str, List[str]]:
    """
    Get guidelines for crafting effective apology messages based on relationship and severity.
    """
    
    base_guidelines = {
        "essential_elements": [
            "Accept full responsibility without excuses",
            "Acknowledge the specific harm caused", 
            "Express genuine remorse and regret",
            "Commit to specific changes or actions",
            "Ask for forgiveness (but don't demand it)"
        ],
        "avoid": [
            "Making excuses or justifications",
            "Blaming the other person ('I'm sorry you felt...')",
            "Minimizing the impact ('It wasn't that bad')",
            "Rushing them to forgive you",
            "Making it about your feelings ('I feel terrible')"
        ],
        "tone_tips": [
            "Be sincere and heartfelt, not dramatic",
            "Match the seriousness of your tone to the situation",
            "Avoid overly formal language unless appropriate",
            "Use 'I' statements to take ownership",
            "Be specific rather than vague"
        ]
    }
    
    # Adjust based on relationship type
    if relationship_type == "romantic":
        base_guidelines["relationship_specific"] = [
            "Acknowledge impact on trust and intimacy",
            "Reaffirm your love and commitment",
            "Be prepared for an emotional conversation",
            "Consider couples counseling if appropriate"
        ]
    elif relationship_type == "family":
        base_guidelines["relationship_specific"] = [
            "Show respect for family values and traditions",
            "Acknowledge disappointment to family reputation",
            "Emphasize long-term family bonds",
            "Consider family dynamics in your approach"
        ]
    elif relationship_type == "friend":
        base_guidelines["relationship_specific"] = [
            "Acknowledge the betrayal of friendship trust",
            "Reaffirm the value of the friendship",
            "Be genuine rather than overly formal",
            "Give them space to process"
        ]
    elif relationship_type == "colleague":
        base_guidelines["relationship_specific"] = [
            "Maintain professional boundaries",
            "Focus on work impact and team dynamics",
            "Commit to professional behavior standards",
            "Keep emotions controlled and appropriate"
        ]
    
    # Adjust based on severity
    if severity >= 8:
        base_guidelines["high_severity_additions"] = [
            "Consider professional mediation or counseling",
            "Be prepared for a longer reconciliation process",
            "Take concrete action before expecting forgiveness",
            "Understand they may need significant time to heal"
        ]
    elif severity >= 6:
        base_guidelines["moderate_severity_additions"] = [
            "Plan for multiple conversations over time",
            "Show consistent change in behavior",
            "Be patient with their healing process"
        ]
    
    return base_guidelines
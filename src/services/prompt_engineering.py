# src/services/prompt_engineering.py
from typing import List, Dict, Optional
from enum import Enum, auto

class BusinessType(Enum):
    B2C = auto()
    B2B = auto()
    RESEARCH = auto()

class Framework(Enum):
    AIDA = auto()
    PAS = auto()
    FAB = auto()
    STAR = auto()
    BAB = auto()
    PASTOR = auto()
    QUEST = auto()

class PresentationRequest:
    def __init__(
        self,
        company_name: str,
        person_name: str,
        business_type: BusinessType,
        domain_type: str,
        framework: Framework
    ):
        self.company_name = company_name
        self.person_name = person_name
        self.business_type = business_type
        self.domain_type = domain_type
        self.framework = framework

class PromptEngineering:
    def __init__(self):
        self.presentation_templates: Dict[str, str] = {
            'B2C': """
            Strategic Pitch for Direct Consumers:
            Company: {company_name}
            
            Welcome Message:
            Greetings {person_name}, let me introduce {company_name}'s unique value proposition.
            
            Industry Context ({domain_type}):
            {context_summary}
            
            Value Points:
            1. Consumer-Focused Solutions: {key_benefits}
            2. Accessible Technology: Bringing enterprise-grade AI to everyday users
            3. Personalized Experience: Tailored to individual consumer needs
            
            Framework ({framework}):
            {framework_points}
            
            Next Steps:
            {action_items}
            """,
            
            'B2B': """
            Enterprise Solution Presentation:
            Partner: {company_name}
            
            Executive Summary:
            Attention {person_name}, I'm presenting a transformative B2B partnership opportunity.
            
            Market Position ({domain_type}):
            {context_summary}
            
            Enterprise Value Proposition:
            1. Scalable Infrastructure: {key_benefits}
            2. Integration Capabilities: Seamless connection with existing systems
            3. ROI Focus: Clear metrics and performance indicators
            
            Strategic Framework ({framework}):
            {framework_points}
            
            Partnership Roadmap:
            {action_items}
            """,
            
            'RESEARCH': """
            Research & Innovation Brief:
            Institution: {company_name}
            
            Research Context:
            Esteemed {person_name}, presenting our research-focused capabilities.
            
            Domain Specifics ({domain_type}):
            {context_summary}
            
            Research Applications:
            1. Data Analysis: {key_benefits}
            2. Methodology Integration: Advanced research tools and frameworks
            3. Academic Collaboration: Research partnership opportunities
            
            Analytical Framework ({framework}):
            {framework_points}
            
            Research Directions:
            {action_items}
            """
        }

        self.consulting_templates: Dict[str, str] = {
            'B2C': """
            Consumer Advisory Framework:
            Client: {company_name}
            
            Consultation Focus:
            {demand}
            
            Market Analysis:
            {context_summary}
            
            Solution Path:
            1. Consumer Behavior Analysis
            2. Market Positioning Strategy
            3. Implementation Roadmap
            
            Framework Application ({framework}):
            {framework_points}
            """,
            
            'B2B': """
            Enterprise Consulting Brief:
            Organization: {company_name}
            
            Strategic Focus:
            {demand}
            
            Industry Context:
            {context_summary}
            
            Business Solution:
            1. Organizational Assessment
            2. Strategic Recommendations
            3. Implementation Framework
            
            Methodology ({framework}):
            {framework_points}
            """
        }

    def format_context(self, context_list: List[str]) -> str:
        """Format context items into a cohesive summary"""
        return "\n".join([f"• {item}" for item in context_list])

    def get_framework_points(self, framework: Framework, business_type: BusinessType, domain: str) -> str:
        """Generate framework-specific points based on business context"""
        framework_content = {
            Framework.AIDA: {
                BusinessType.B2C: {
                    'TECH': [
                        "Attention: Cutting-edge AI solutions for daily needs",
                        "Interest: Personalized technology adaptation",
                        "Desire: Seamless integration with lifestyle",
                        "Action: Start with a free trial"
                    ]
                },
                BusinessType.B2B: {
                    'TECH': [
                        "Attention: Enterprise-grade AI infrastructure",
                        "Interest: Scalable business solutions",
                        "Desire: Competitive advantage through technology",
                        "Action: Schedule a demo"
                    ]
                }
            }
        }

        try:
            points = framework_content[framework][business_type][domain]
            return "\n".join([f"• {point}" for point in points])
        except KeyError:
            return self.get_default_framework_points(framework)

    def get_default_framework_points(self, framework: Framework) -> str:
        """Provide default framework points if specific context not found"""
        default_points = {
            Framework.AIDA: [
                "Attention: Capture interest with our innovative solution",
                "Interest: Demonstrate unique value proposition and relevance",
                "Desire: Highlight specific benefits and advantages",
                "Action: Clear next steps and engagement path"
            ],
            Framework.PAS: [
                "Problem: Identify current challenges and pain points",
                "Agitation: Explore implications and consequences",
                "Solution: Present our comprehensive approach"
            ]
        }
        
        points = default_points.get(framework, ["Point 1", "Point 2", "Point 3"])
        return "\n".join([f"• {point}" for point in points])

    def generate_presentation_prompt(self, req: PresentationRequest, context: List[str]) -> str:
        """Generate a presentation prompt based on business type and context"""
        template = self.presentation_templates.get(
            req.business_type.name, 
            self.presentation_templates['B2C']
        )
        
        return template.format(
            company_name=req.company_name,
            person_name=req.person_name,
            domain_type=req.domain_type,
            context_summary=self.format_context(context),
            key_benefits=context[0] if context else "Customized solutions",
            framework=req.framework.name,
            framework_points=self.get_framework_points(
                req.framework,
                req.business_type,
                req.domain_type
            ),
            action_items=self.generate_action_items(req.business_type, req.domain_type)
        )

    def generate_action_items(self, business_type: BusinessType, domain: str) -> str:
        """Generate relevant action items based on business context"""
        action_items: Dict[BusinessType, Dict[str, List[str]]] = {
            BusinessType.B2C: {
                'TECH': [
                    "Schedule a personal demo",
                    "Start free trial",
                    "Join user community"
                ]
            },
            BusinessType.B2B: {
                'TECH': [
                    "Book technical consultation",
                    "Request pricing proposal",
                    "Schedule integration assessment"
                ]
            }
        }

        items = action_items.get(business_type, {}).get(domain, ["Contact us", "Request more information"])
        return "\n".join([f"• {item}" for item in items])
